"""
Daily MLB 2026 results updater.

Changed from the original: writes straight to R2 instead of
docs/data/baseball/ in git (that's what was slowly re-growing the repo
back toward GitHub Pages' 1GB deployment limit every day). Also adds
skip-if-already-uploaded logic -- the original re-fetched and rewrote
EVERY completed game from MLB's API on every single run, even games
finished weeks ago; this only fetches games not already in R2.

Hardening added on top of that:
  - All HTTP calls go through a shared requests.Session with a real
    User-Agent (statsapi.mlb.com has been observed deprioritizing/
    blocking default python-requests UAs, especially from CI IP ranges
    like GitHub Actions runners).
  - Every request has an explicit timeout, retries with backoff, and
    raise_for_status() so a 403/429/5xx or malformed body is a loud,
    logged failure instead of silently becoming an empty dict.
  - Schedule fetches that fail after retries are recorded and reported
    at the end (not just skipped, which used to look identical to "no
    games that day").

Doubleheader fix (found via diagnostics -- 23 confirmed collisions):
  The old filename was "{date}_{away}_{home}.json" with no game
  identifier, so a doubleheader (two different gamePks, same date,
  same matchup) collided on the same R2 key. Because existing_keys is
  a snapshot taken before the run starts, BOTH games of a doubleheader
  would pass the "already have" check as new, get fetched, and the
  second one silently overwrote the first's box score in R2 --
  permanent, silent data loss for one game of every doubleheader.

  Fix: filenames now include gamePk, so every game gets a guaranteed-
  unique key. To avoid re-fetching all ~2000 already-saved games (which
  were saved under the OLD filename format and won't match the new
  key), this script also recognizes old-format keys as "already have"
  UNLESS that date+matchup is one of the known-ambiguous doubleheader
  cases (multiple gamePks sharing the same old-style id) -- those are
  deliberately treated as new so both games of the doubleheader get
  correctly fetched and saved separately, one time, under the new
  collision-proof key format. Old-format files for those corrected
  games become orphaned/unused in R2; they're harmless but you can
  clean them up manually later if you want (their keys are logged
  below).

Needs the same R2 secrets already configured in this repo:
  R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
"""

import io
import json
import os
import sys
import time
from collections import defaultdict

import boto3
import requests
from botocore.config import Config

SEASON = "2026"
BUCKET_NAME = "sporting-almanac-data"
R2_PREFIX = "baseball"
SEASON_KEY = f"{R2_PREFIX}/seasons/{SEASON}.json"
BOXSCORE_PREFIX = f"{R2_PREFIX}/boxscores/{SEASON}/"

# TEMPORARY: forces every game on/after this date to be freshly re-fetched
# and overwritten this run, bypassing the "already have" skip logic
# entirely, to guarantee correct data lands in R2 regardless of root
# cause. Remove this (set back to None) after confirming the backfill
# worked -- leaving it in place means every daily run will keep
# re-fetching this whole window forever, growing more expensive every
# day and defeating the skip-cache optimization.
FORCE_REFRESH_SINCE = "2026-07-27"

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.5

TEAM_ID_MAP = {
    109: "ARI", 144: "ATL", 110: "BAL", 111: "BOS", 112: "CHC",
    145: "CHW", 113: "CIN", 114: "CLE", 115: "COL", 116: "DET",
    117: "HOU", 118: "KC", 108: "LAA", 119: "LAD", 146: "MIA",
    158: "MIL", 142: "MIN", 121: "NYM", 147: "NYY", 133: "ATH",
    143: "PHI", 134: "PIT", 135: "SD", 136: "SEA", 137: "SF",
    138: "STL", 139: "TB", 140: "TEX", 141: "TOR", 120: "WSH"
}

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
})


def fetch_json(url, retries=MAX_RETRIES):
    """GET a URL and parse JSON, with retries/backoff and loud failures.

    Returns (data, ok). ok=False means every attempt failed -- caller
    decides what to do (skip vs abort), but the failure is always
    printed so it shows up in the workflow log.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json(), True
        except requests.HTTPError as e:
            last_error = e
            status = e.response.status_code if e.response is not None else "?"
            print(f"    [attempt {attempt}/{retries}] HTTP {status} for {url}")
        except requests.RequestException as e:
            last_error = e
            print(f"    [attempt {attempt}/{retries}] request error for {url}: {e}")
        except ValueError as e:
            # response.json() failed to parse -- likely an HTML error/CAPTCHA page
            last_error = e
            snippet = resp.text[:200].replace("\n", " ") if "resp" in locals() else ""
            print(f"    [attempt {attempt}/{retries}] bad JSON from {url}: {e} | body starts: {snippet!r}")

        if attempt < retries:
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    print(f"  GIVING UP on {url} after {retries} attempts: {last_error}")
    return {}, False


def get_client():
    endpoint = os.environ.get("R2_ENDPOINT")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

    missing = [name for name, val in [
        ("R2_ENDPOINT", endpoint),
        ("R2_ACCESS_KEY_ID", access_key),
        ("R2_SECRET_ACCESS_KEY", secret_key),
    ] if not val]
    if missing:
        print(f"Missing environment variable(s): {', '.join(missing)}")
        sys.exit(1)

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def get_existing_boxscore_keys(client):
    """Games already uploaded -- skip re-fetching these from MLB's API
    entirely, unlike the original script which redid all of them daily."""
    existing = set()
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=BOXSCORE_PREFIX):
        for obj in page.get("Contents", []):
            existing.add(obj["Key"])
    return existing


def split_legacy_key(key):
    """Given an R2 key under BOXSCORE_PREFIX, return (old_style_id, is_old_format).

    Old format:  {date}_{away}_{home}.json           -> 3 underscore parts
    New format:  {date}_{away}_{home}_{gamePk}.json  -> 4 underscore parts
    old_style_id is always "{date}_{away}_{home}" so both formats are
    comparable against a freshly-computed old_style_id.
    """
    fname = key[len(BOXSCORE_PREFIX):]
    if not fname.endswith(".json"):
        return None, False
    core = fname[:-5]
    parts = core.split("_")
    if len(parts) == 3:
        return core, True
    if len(parts) == 4:
        return "_".join(parts[:3]), False
    return None, False


def put_json(client, key, data):
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(Bucket=BUCKET_NAME, Key=key, Body=body, ContentType="application/json")


def main():
    client = get_client()

    print("Checking R2 for games already uploaded...")
    existing_keys = get_existing_boxscore_keys(client)
    print(f"{len(existing_keys)} game(s) already in R2 for {SEASON}.")
    if FORCE_REFRESH_SINCE:
        print(f"FORCE REFRESH ACTIVE: every Final game on/after {FORCE_REFRESH_SINCE} "
              f"will be freshly re-fetched and overwritten this run, ignoring skip-cache.")

    # Build a lookup of old-style ids -> actual R2 key, for legacy-key
    # migration matching (see module docstring).
    old_style_to_key = {}
    for key in existing_keys:
        old_style_id, is_old_format = split_legacy_key(key)
        if old_style_id and is_old_format:
            old_style_to_key[old_style_id] = key

    print("Downloading MLB 2026 schedule...")
    month_ranges = [
        ("2026-03-25", "2026-03-31"), ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-31"), ("2026-06-01", "2026-06-30"),
        ("2026-07-01", "2026-07-31"), ("2026-08-01", "2026-08-31"),
        ("2026-09-01", "2026-09-30"), ("2026-10-01", "2026-10-05"),
    ]

    all_dates = {}
    schedule_fetch_failures = []
    for start, end in month_ranges:
        url = (f"https://statsapi.mlb.com/api/v1/schedule?"
               f"sportId=1&season={SEASON}&gameType=R&startDate={start}&endDate={end}")
        data, ok = fetch_json(url)
        if not ok:
            schedule_fetch_failures.append((start, end))
            print(f"  {start} to {end}: FAILED to fetch -- 0 dates recorded (see errors above)")
            continue
        for date_block in data.get("dates", []):
            all_dates[date_block["date"]] = date_block
        print(f"  {start} to {end}: {len(data.get('dates', []))} dates")

    print(f"Total date blocks: {len(all_dates)}")
    if schedule_fetch_failures:
        print(f"WARNING: {len(schedule_fetch_failures)} month range(s) failed to fetch entirely "
              f"and are NOT reflected in this run: {schedule_fetch_failures}")

    # Pre-pass (no network calls): figure out which old-style ids are
    # ambiguous -- i.e. correspond to more than one gamePk in the
    # schedule data (doubleheaders). For those, we deliberately do NOT
    # trust a legacy-key match, since the single old file could only
    # ever have belonged to one of the two games and we can't tell
    # which. Both games get treated as new and saved separately under
    # the new gamePk-qualified key.
    old_style_gamepks = defaultdict(set)
    for date_block in all_dates.values():
        game_date = date_block.get("date")
        for game in date_block.get("games", []):
            if not isinstance(game, dict):
                continue
            if game.get("status", {}).get("abstractGameState", "") != "Final":
                continue
            try:
                home = game["teams"]["home"]
                away = game["teams"]["away"]
                home_id = home.get("team", {}).get("id")
                away_id = away.get("team", {}).get("id")
                if not home_id or not away_id:
                    continue
                home_code = TEAM_ID_MAP.get(home_id, "UNK")
                away_code = TEAM_ID_MAP.get(away_id, "UNK")
                old_style_id = f"{game_date}_{away_code}_{home_code}"
                old_style_gamepks[old_style_id].add(game.get("gamePk"))
            except (KeyError, TypeError):
                continue

    ambiguous_old_style_ids = {k for k, v in old_style_gamepks.items() if len(v) > 1}
    if ambiguous_old_style_ids:
        print(f"Doubleheader dates detected this run (ambiguous legacy keys, "
              f"will be freshly fetched/split): {len(ambiguous_old_style_ids)}")
        for oid in sorted(ambiguous_old_style_ids):
            print(f"    {oid} -- gamePks {sorted(old_style_gamepks[oid])}")

    season_games = []
    saved = 0
    skipped_not_final = 0
    skipped_already_have = 0
    failed = 0
    live_fetch_failures = []
    migrated_legacy_matches = 0
    doubleheader_splits_fetched = 0

    # Diagnostics: track every NEW-format r2_key this run actually
    # matches to a Final game, and detect any lingering filename
    # collisions (should be ~zero now that gamePk is in the key).
    seen_keys_this_run = set()
    matched_legacy_keys = set()
    game_pk_by_key = {}
    collisions = []
    orphaned_legacy_keys_used_for_fix = set()

    for date_block in sorted(all_dates.values(), key=lambda x: x["date"]):
        game_date = date_block.get("date")

        for game in date_block.get("games", []):
            if not isinstance(game, dict):
                continue

            try:
                game_pk = game.get("gamePk")
                home = game["teams"]["home"]
                away = game["teams"]["away"]

                if not isinstance(home, dict) or not isinstance(away, dict):
                    continue

                home_team = home.get("team", {}).get("name", "UNK")
                away_team = away.get("team", {}).get("name", "UNK")
                home_id = home.get("team", {}).get("id")
                away_id = away.get("team", {}).get("id")

                if not home_id or not away_id:
                    continue

                home_code = TEAM_ID_MAP.get(home_id, "UNK")
                away_code = TEAM_ID_MAP.get(away_id, "UNK")

                venue = game.get("venue", {}).get("name", "")
                status = game.get("status", {}).get("detailedState", "")
                abstract_state = game.get("status", {}).get("abstractGameState", "")

                old_style_id = f"{game_date}_{away_code}_{home_code}"

                # gamePk included so doubleheaders never collide (see
                # module docstring for the historical bug this fixes).
                filename = f"{game_date}_{away_code}_{home_code}_{game_pk}.json"
                r2_key = f"{BOXSCORE_PREFIX}{filename}"

                # Sanity check -- should never fire now that gamePk is
                # part of the key. If it does, gamePk itself is missing
                # or duplicated in the API response, which is a
                # different and more serious problem worth investigating.
                if r2_key in game_pk_by_key and game_pk_by_key[r2_key] != game_pk:
                    collisions.append((r2_key, game_pk_by_key[r2_key], game_pk))
                game_pk_by_key[r2_key] = game_pk

                if abstract_state != "Final":
                    skipped_not_final += 1
                    continue

                seen_keys_this_run.add(r2_key)

                # Decide "already have" status:
                #   1. New-format key already in R2 -> definitely have it.
                #   2. Old-format legacy key exists AND this old_style_id
                #      is unambiguous (not a doubleheader collision) ->
                #      treat as already have, use the REAL legacy filename
                #      so the season index still points at a file that
                #      actually exists.
                #   3. Otherwise (including ambiguous doubleheader ids) ->
                #      not already have; fetch and save fresh under the
                #      new key.
                already_have = False
                effective_filename = filename
                force_refresh = bool(FORCE_REFRESH_SINCE) and game_date >= FORCE_REFRESH_SINCE

                if not force_refresh:
                    if r2_key in existing_keys:
                        already_have = True
                    elif (old_style_id in old_style_to_key
                            and old_style_id not in ambiguous_old_style_ids):
                        already_have = True
                        legacy_key = old_style_to_key[old_style_id]
                        matched_legacy_keys.add(legacy_key)
                        effective_filename = legacy_key[len(BOXSCORE_PREFIX):]
                        migrated_legacy_matches += 1
                    elif old_style_id in ambiguous_old_style_ids:
                        doubleheader_splits_fetched += 1
                        if old_style_id in old_style_to_key:
                            orphaned_legacy_keys_used_for_fix.add(old_style_to_key[old_style_id])

                if already_have:
                    skipped_already_have += 1
                    home_score = home.get("score", 0) or 0
                    away_score = away.get("score", 0) or 0
                    season_games.append({
                        "game_id": game_pk, "date": game_date,
                        "home_team": home_team, "away_team": away_team,
                        "home_code": home_code, "away_code": away_code,
                        "home_score": home_score, "away_score": away_score,
                        "venue": venue, "status": status, "game_file": effective_filename
                    })
                    continue

                live_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
                live_data, ok = fetch_json(live_url)
                time.sleep(0.2)

                if not ok:
                    print(f"  FAILED to fetch live feed for game {game_pk} (see errors above)")
                    live_fetch_failures.append(game_pk)
                    failed += 1
                    continue

                if not isinstance(live_data, dict) or "liveData" not in live_data:
                    print(f"  Unexpected live_data shape for {game_pk}: "
                          f"keys={list(live_data)[:10] if isinstance(live_data, dict) else type(live_data)}")
                    failed += 1
                    continue

                home_score = 0
                away_score = 0
                try:
                    linescore = live_data["liveData"]["linescore"]
                    home_score = linescore["teams"]["home"].get("runs", 0) or 0
                    away_score = linescore["teams"]["away"].get("runs", 0) or 0
                except (KeyError, TypeError):
                    try:
                        home_score = home.get("score", 0) or 0
                        away_score = away.get("score", 0) or 0
                    except (KeyError, TypeError):
                        pass

                game_json = {
                    "game_id": game_pk, "date": game_date, "status": status, "venue": venue,
                    "home_team": {"name": home_team, "code": home_code, "score": home_score},
                    "away_team": {"name": away_team, "code": away_code, "score": away_score},
                    "liveData": live_data.get("liveData", {})
                }

                put_json(client, r2_key, game_json)
                print(f"  Saved {filename} ({away_score}-{home_score})")
                saved += 1

                season_games.append({
                    "game_id": game_pk, "date": game_date,
                    "home_team": home_team, "away_team": away_team,
                    "home_code": home_code, "away_code": away_code,
                    "home_score": home_score, "away_score": away_score,
                    "venue": venue, "status": status, "game_file": filename
                })

            except Exception as e:
                print(f"  FAILED game {game.get('gamePk', '?')}: {e}")
                failed += 1

    season_games.sort(key=lambda x: (x["date"], x["away_team"]))
    put_json(client, SEASON_KEY, season_games)

    print("")
    print("DONE")
    print(f"  Saved (new):               {saved}")
    print(f"    of which doubleheader-split fetches: {doubleheader_splits_fetched}")
    print(f"  Already had:               {skipped_already_have}")
    print(f"    of which matched via legacy (old-format) key: {migrated_legacy_matches}")
    print(f"  Not final yet:             {skipped_not_final}")
    print(f"  Failed (live feed etc):    {failed}")
    print(f"  Total in season file:      {len(season_games)}")
    if schedule_fetch_failures:
        print(f"  Schedule ranges FAILED:    {schedule_fetch_failures}")
    if live_fetch_failures:
        print(f"  Live feed game IDs FAILED: {live_fetch_failures}")
    if orphaned_legacy_keys_used_for_fix:
        print(f"  Old-format files now orphaned by doubleheader fix "
              f"(safe to delete manually, data was re-saved under new keys):")
        for k in sorted(orphaned_legacy_keys_used_for_fix):
            print(f"    {k}")

    # Diagnostic: keys that exist in R2 (old or new format) but were
    # never matched to a Final game this run at all -- e.g. Spring
    # Training games from before your schedule range starts. Expected
    # to be non-empty and roughly stable run to run; a growing count
    # over time would indicate a real problem.
    accounted_for = seen_keys_this_run | matched_legacy_keys
    orphaned_keys = existing_keys - accounted_for
    print("")
    print(f"DIAGNOSTIC: {len(existing_keys)} keys in R2 vs {len(accounted_for)} "
          f"accounted for this run -- {len(orphaned_keys)} orphaned (in R2, not matched)")
    if orphaned_keys:
        sample = sorted(orphaned_keys)[:25]
        print(f"  Sample of orphaned keys (up to 25 of {len(orphaned_keys)}):")
        for k in sample:
            print(f"    {k}")
        if len(orphaned_keys) > 25:
            print(f"    ...and {len(orphaned_keys) - 25} more")

    if collisions:
        print(f"DIAGNOSTIC: {len(collisions)} filename collision(s) on NEW-format keys "
              f"(should be 0 -- indicates gamePk itself is missing/duplicated in the API):")
        for r2_key, first_pk, second_pk in collisions[:25]:
            print(f"    {r2_key}: gamePk {first_pk} then {second_pk}")

    # Make the failure visible to the Actions run status rather than
    # only in logs -- a completely failed schedule fetch means this
    # run produced garbage/incomplete data.
    if schedule_fetch_failures and not all_dates:
        print("FATAL: could not fetch ANY schedule data this run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
