#!/usr/bin/env python3
import os
import json
import requests
import csv
import io

START_YEAR = 1970
END_YEAR = 1970

OUT_ROOT = "docs/data/nfl"
SEASONS_DIR = os.path.join(OUT_ROOT, "seasons")

# 🔥 PERMANENT SNAPSHOT (this will NOT move)
BASE = "https://cdn.jsdelivr.net/gh/nflverse/nflverse-data@v0.0.0/data/games.csv"

def mkdirs():
    os.makedirs(SEASONS_DIR, exist_ok=True)

def fetch_csv():
    print("Downloading NFL dataset...")

    r = requests.get(BASE)
    r.raise_for_status()

    return list(csv.DictReader(io.StringIO(r.text)))

def build_season(year, data):
    games = []

    for g in data:
        try:
            if int(g["season"]) != year:
                continue

            if g.get("game_type") not in ["REG", "POST"]:
                continue

            games.append({
                "season": year,
                "game_id": g["game_id"],
                "week": g["week"],
                "date": g["gameday"],
                "home_team": g["home_team"],
                "away_team": g["away_team"],
                "home_points": int(g["home_score"]) if g["home_score"] else None,
                "away_points": int(g["away_score"]) if g["away_score"] else None,
                "season_type": "postseason" if g["game_type"] == "POST" else "regular"
            })
        except:
            continue

    print(f"{year}: {len(games)} games")
    return games

def write_season(year, games):
    out_file = os.path.join(SEASONS_DIR, f"{year}.json")

    data = {
        "season": year,
        "source": "nflverse-snapshot",
        "games": games
    }

    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"wrote {year}.json")

def main():
    mkdirs()
    data = fetch_csv()

    for year in range(START_YEAR, END_YEAR + 1):
        games = build_season(year, data)
        write_season(year, games)

if __name__ == "__main__":
    main()
