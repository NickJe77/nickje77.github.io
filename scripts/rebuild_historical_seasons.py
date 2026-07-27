"""
Rebuilds baseball/seasons/YYYY.json for 1946-2025 from the real
per-game boxscore data already in R2 (baseball/boxscores/YYYY/*.json),
which has genuine scores/dates/teams -- unlike whatever was previously
sitting at seasons/YYYY.json for these years (confirmed wrong: player
season-stats data, not a game schedule).

2026 is deliberately excluded -- the daily MLB script already
maintains that one correctly.

Resumable by year: skips any year whose seasons/YYYY.json already has
the correct game-schedule shape, so a re-run after a timeout picks up
where it left off instead of redoing finished years.

Needs the same R2 secrets already configured in this repo:
  R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.config import Config

BUCKET_NAME = "sporting-almanac-data"
R2_PREFIX = "baseball"
NUM_WORKERS = 24
YEARS = list(range(1946, 2026))  # 2026 excluded, already correct


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
        config=Config(signature_version="s3v4", max_pool_connections=NUM_WORKERS * 2),
        region_name="auto",
    )


def load_team_map(client):
    """code -> canonical full name, from the already-migrated teams.json."""
    obj = client.get_object(Bucket=BUCKET_NAME, Key=f"{R2_PREFIX}/teams.json")
    teams = json.loads(obj["Body"].read())
    code_map = {}
    for team in teams:
        name = team.get("name")
        for code in team.get("codes", []):
            code_map[code] = name
    return code_map


def season_already_rebuilt(client, year, team_map):
    """Checks whether seasons/YYYY.json already has the correct
    game-schedule shape AND is already MLB-only, so finished years get
    skipped on a re-run but years still containing Negro League/All-Star
    games (from before the MLB-only filter was added) get reprocessed."""
    key = f"{R2_PREFIX}/seasons/{year}.json"
    try:
        obj = client.get_object(Bucket=BUCKET_NAME, Key=key)
        data = json.loads(obj["Body"].read())
        if not (isinstance(data, list) and len(data) > 0
                and isinstance(data[0], dict)
                and "date" in data[0] and "home_score" in data[0]):
            return False
        # Every code must be a real MLB team -- if any game slipped
        # through from before this filter existed, treat the year as
        # not yet correctly rebuilt.
        for g in data:
            if g.get("home_code") not in team_map or g.get("away_code") not in team_map:
                return False
        return True
    except Exception:
        return False


def list_boxscore_keys(client, year):
    keys = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=f"{R2_PREFIX}/boxscores/{year}/"):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


def fetch_and_extract(client, key, team_map):
    try:
        obj = client.get_object(Bucket=BUCKET_NAME, Key=key)
        d = json.loads(obj["Body"].read())
    except Exception as e:
        return None, str(e)

    home_code = d.get("home_code")
    away_code = d.get("away_code")
    home_score = d.get("home_score")
    away_score = d.get("away_score")
    date = d.get("date")

    if not all([home_code, away_code, date]) or home_score is None or away_score is None:
        return None, "missing required field"

    # MLB-only: both teams must be genuine MLB franchises per
    # teams.json. This excludes Negro League games, All-Star games
    # (ASE/ASF/ASP/ASW-style codes), and other non-regular-season
    # exhibition games that were mixed into the same boxscore data.
    if home_code not in team_map or away_code not in team_map:
        return None, "non-MLB game (excluded by design)"

    home_team = team_map.get(home_code, home_code)
    away_team = team_map.get(away_code, away_code)

    game_file = key.split("/")[-1]

    return {
        "date": date,
        "home_team": home_team,
        "away_team": away_team,
        "home_code": home_code,
        "away_code": away_code,
        "home_score": home_score,
        "away_score": away_score,
        "venue": "",  # not present in the source data for these years
        "status": "Final",
        "game_file": game_file,
    }, None


def rebuild_year(client, team_map, year):
    keys = list_boxscore_keys(client, year)
    if not keys:
        print(f"  {year}: no boxscore files found, skipping.")
        return 0, 0, 0

    games = []
    failed = 0
    excluded = 0

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(fetch_and_extract, client, k, team_map): k for k in keys}
        for future in as_completed(futures):
            result, error = future.result()
            if result:
                games.append(result)
            elif error == "non-MLB game (excluded by design)":
                excluded += 1
            else:
                failed += 1

    games.sort(key=lambda g: (g["date"], g["away_team"]))

    body = json.dumps(games, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(
        Bucket=BUCKET_NAME, Key=f"{R2_PREFIX}/seasons/{year}.json",
        Body=body, ContentType="application/json",
    )

    print(f"  {year}: {len(games)} MLB game(s) rebuilt, {excluded} non-MLB game(s) excluded, {failed} failed")
    return len(games), failed, excluded


def main():
    client = get_client()

    print("Loading team code -> name map from teams.json...")
    team_map = load_team_map(client)
    print(f"{len(team_map)} code(s) mapped.")

    start_time = time.time()
    total_games = 0
    total_failed = 0
    total_excluded = 0
    years_done = 0
    years_skipped = 0

    for year in YEARS:
        if season_already_rebuilt(client, year, team_map):
            years_skipped += 1
            continue

        print(f"Rebuilding {year}...")
        games, failed, excluded = rebuild_year(client, team_map, year)
        total_games += games
        total_failed += failed
        total_excluded += excluded
        years_done += 1

        elapsed = time.time() - start_time
        print(f"  [{years_done} year(s) done this run, {years_skipped} already done, "
              f"{elapsed/60:.1f} min elapsed]")

    print(f"\nDone this run. {years_done} year(s) rebuilt, {years_skipped} already "
          f"had correct MLB-only data, {total_games} total MLB game(s), "
          f"{total_excluded} non-MLB game(s) excluded, {total_failed} failed.")


if __name__ == "__main__":
    main()
