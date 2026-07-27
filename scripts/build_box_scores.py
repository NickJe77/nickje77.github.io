"""
Augments every boxscores/YYYY/*.json file in R2 with real batting and
pitching lines (away_batting, home_batting, away_pitching, home_pitching),
built from the games/YYYY/{game_id}.json files (same game_id in both --
verified directly against real data) and player names resolved via
biofile0.csv.

Available fields are genuinely limited by the source data: batting has
AB/H/BB/SO (no Runs or RBI -- not tracked in this dataset), pitching has
IP/H/BB/SO (no Earned Runs). This does NOT fabricate those missing
stats -- baseball-game.html is updated separately to show only what's
real.

Resumable: skips any boxscore file that's already been augmented (has
an away_batting key), so a re-run after a timeout continues rather than
restarting.

Needs the same R2 secrets already configured in this repo:
  R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
"""

import csv
import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.config import Config

BUCKET_NAME = "sporting-almanac-data"
R2_PREFIX = "baseball"
NUM_WORKERS = 16
YEARS = list(range(1946, 2027))


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


def load_player_names(client):
    """player_id -> "First Last", from biofile0.csv (same source
    build_baseball_players.py already uses for this)."""
    obj = client.get_object(Bucket=BUCKET_NAME, Key=f"{R2_PREFIX}/biofile0.csv")
    text = obj["Body"].read().decode("utf-8", errors="replace")
    names = {}
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        pid = (row.get("id") or "").strip()
        first = (row.get("usename") or "").strip()
        last = (row.get("lastname") or "").strip()
        if pid and first and last:
            names[pid] = f"{first} {last}"
    return names


def list_boxscore_keys(client, year):
    keys = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=f"{R2_PREFIX}/boxscores/{year}/"):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


def build_batting_line(player_id, stats, names):
    return {
        "name": names.get(player_id, player_id),
        "player_id": player_id,
        "AB": stats.get("AB", 0),
        "H": stats.get("H", 0),
        "BB": stats.get("BB", 0),
        "SO": stats.get("SO", 0),
    }


def build_pitching_line(player_id, stats, names):
    return {
        "name": names.get(player_id, player_id),
        "player_id": player_id,
        "IP": stats.get("IP", "0.0"),
        "H": stats.get("H", 0),
        "BB": stats.get("BB", 0),
        "SO": stats.get("SO", 0),
    }


def augment_one(client, key, names):
    try:
        obj = client.get_object(Bucket=BUCKET_NAME, Key=key)
        box = json.loads(obj["Body"].read())
    except Exception as e:
        return key, False, f"read boxscore failed: {e}"

    if "away_batting" in box:
        return key, True, "already done"

    game_id = box.get("game_id")
    season = box.get("season")
    if not game_id or not season:
        return key, False, "missing game_id/season"

    games_key = f"{R2_PREFIX}/games/{season}/{game_id}.json"
    try:
        obj2 = client.get_object(Bucket=BUCKET_NAME, Key=games_key)
        game_detail = json.loads(obj2["Body"].read())
    except Exception as e:
        return key, False, f"no matching games/ file: {e}"

    away_batting = [
        build_batting_line(p.get("player_id"), p, names)
        for p in game_detail.get("batters_away", []) if p.get("player_id")
    ]
    home_batting = [
        build_batting_line(p.get("player_id"), p, names)
        for p in game_detail.get("batters_home", []) if p.get("player_id")
    ]
    away_pitching = [
        build_pitching_line(p.get("player_id"), p, names)
        for p in game_detail.get("pitchers_away", []) if p.get("player_id")
    ]
    home_pitching = [
        build_pitching_line(p.get("player_id"), p, names)
        for p in game_detail.get("pitchers_home", []) if p.get("player_id")
    ]

    box["away_batting"] = away_batting
    box["home_batting"] = home_batting
    box["away_pitching"] = away_pitching
    box["home_pitching"] = home_pitching

    try:
        body = json.dumps(box, ensure_ascii=False, indent=2).encode("utf-8")
        client.put_object(Bucket=BUCKET_NAME, Key=key, Body=body, ContentType="application/json")
    except Exception as e:
        return key, False, f"write failed: {e}"

    return key, True, None


def process_year(client, names, year):
    keys = list_boxscore_keys(client, year)
    if not keys:
        print(f"  {year}: no boxscore files found, skipping.")
        return 0, 0

    done = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(augment_one, client, k, names): k for k in keys}
        for future in as_completed(futures):
            key, success, note = future.result()
            if success:
                done += 1
            else:
                failed += 1
                print(f"  FAILED {key}: {note}")

    print(f"  {year}: {done} game(s) augmented/verified, {failed} failed")
    return done, failed


def main():
    client = get_client()

    print("Loading player names from biofile0.csv...")
    names = load_player_names(client)
    print(f"{len(names)} player name(s) loaded.")

    start_time = time.time()
    total_done = 0
    total_failed = 0

    for year in YEARS:
        print(f"Processing {year}...")
        done, failed = process_year(client, names, year)
        total_done += done
        total_failed += failed

        elapsed = time.time() - start_time
        print(f"  [{elapsed/60:.1f} min elapsed, {total_done} total done, {total_failed} total failed]")

    print(f"\nDone this run. {total_done} boxscore(s) augmented/verified, {total_failed} failed.")


if __name__ == "__main__":
    main()
