"""
Daily MLB 2026 results updater.

Changed from the original: writes straight to R2 instead of
docs/data/baseball/ in git (that's what was slowly re-growing the repo
back toward GitHub Pages' 1GB deployment limit every day). Also adds
skip-if-already-uploaded logic -- the original re-fetched and rewrote
EVERY completed game from MLB's API on every single run, even games
finished weeks ago; this only fetches games not already in R2.

Needs the same R2 secrets already configured in this repo:
  R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
"""

import io
import json
import os
import sys
import time

import boto3
import requests
from botocore.config import Config

SEASON = "2026"
BUCKET_NAME = "sporting-almanac-data"
R2_PREFIX = "baseball"
SEASON_KEY = f"{R2_PREFIX}/seasons/{SEASON}.json"
BOXSCORE_PREFIX = f"{R2_PREFIX}/boxscores/{SEASON}/"

TEAM_ID_MAP = {
    109: "ARI", 144: "ATL", 110: "BAL", 111: "BOS", 112: "CHC",
    145: "CHW", 113: "CIN", 114: "CLE", 115: "COL", 116: "DET",
    117: "HOU", 118: "KC", 108: "LAA", 119: "LAD", 146: "MIA",
    158: "MIL", 142: "MIN", 121: "NYM", 147: "NYY", 133: "ATH",
    143: "PHI", 134: "PIT", 135: "SD", 136: "SEA", 137: "SF",
    138: "STL", 139: "TB", 140: "TEX", 141: "TOR", 120: "WSH"
}


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


def put_json(client, key, data):
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(Bucket=BUCKET_NAME, Key=key, Body=body, ContentType="application/json")


def main():
    client = get_client()

    print("Checking R2 for games already uploaded...")
    existing_keys = get_existing_boxscore_keys(client)
    print(f"{len(existing_keys)} game(s) already in R2 for {SEASON}.")

    print("Downloading MLB 2026 schedule...")
    month_ranges = [
        ("2026-03-25", "2026-03-31"), ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-31"), ("2026-06-01", "2026-06-30"),
        ("2026-07-01", "2026-07-31"), ("2026-08-01", "2026-08-31"),
        ("2026-09-01", "2026-09-30"), ("2026-10-01", "2026-10-05"),
    ]

    all_dates = {}
    for start, end in month_ranges:
        url = (f"https://statsapi.mlb.com/api/v1/schedule?"
               f"sportId=1&season={SEASON}&gameType=R&startDate={start}&endDate={end}")
        data = requests.get(url).json()
        for date_block in data.get("dates", []):
            all_dates[date_block["date"]] = date_block
        print(f"  {start} to {end}: {len(data.get('dates', []))} dates")

    print(f"Total date blocks: {len(all_dates)}")

    season_games = []
    saved = 0
    skipped_not_final = 0
    skipped_already_have = 0
    failed = 0

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

                filename = f"{game_date}_{away_code}_{home_code}.json"
                r2_key = f"{BOXSCORE_PREFIX}{filename}"

                if abstract_state != "Final":
                    skipped_not_final += 1
                    continue

                # Games already uploaded to R2 don't need re-fetching --
                # this is the key change from the original, which redid
                # every completed game every single day.
                if r2_key in existing_keys:
                    skipped_already_have += 1
                    # Still add to season_games so the season summary
                    # file stays complete, using the previously-known
                    # scores from the schedule response.
                    home_score = home.get("score", 0) or 0
                    away_score = away.get("score", 0) or 0
                    season_games.append({
                        "game_id": game_pk, "date": game_date,
                        "home_team": home_team, "away_team": away_team,
                        "home_code": home_code, "away_code": away_code,
                        "home_score": home_score, "away_score": away_score,
                        "venue": venue, "status": status, "game_file": filename
                    })
                    continue

                live_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
                live_data = requests.get(live_url).json()
                time.sleep(0.2)

                if not isinstance(live_data, dict) or "liveData" not in live_data:
                    print(f"  Unexpected live_data for {game_pk}")
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
    print(f"  Saved (new):          {saved}")
    print(f"  Already had:          {skipped_already_have}")
    print(f"  Not final yet:        {skipped_not_final}")
    print(f"  Failed:               {failed}")
    print(f"  Total in season file: {len(season_games)}")


if __name__ == "__main__":
    main()
