#!/usr/bin/env python3
import os
import json
import csv

START_YEAR = 1970
END_YEAR = 1970

OUT_ROOT = "docs/data/nfl"
SEASONS_DIR = os.path.join(OUT_ROOT, "seasons")
RAW_FILE = os.path.join(OUT_ROOT, "raw_games.csv")

def mkdirs():
    os.makedirs(SEASONS_DIR, exist_ok=True)

def load_data():
    print("Loading local dataset...")

    with open(RAW_FILE, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

def build_season(year, data):
    games = []

    for g in data:
        try:
            if int(g["season"]) != year:
                continue

            if g["game_type"] not in ["REG", "POST"]:
                continue

            games.append({
                "season": year,
                "game_id": g["game_id"],
                "week": g["week"],
                "date": g["gameday"],
                "home_team": g["home_team"],
                "away_team": g["away_team"],
                "home_points": int(g["home_score"]),
                "away_points": int(g["away_score"]),
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
        "source": "local",
        "games": games
    }

    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"wrote {year}.json")

def main():
    mkdirs()
    data = load_data()

    for year in range(START_YEAR, END_YEAR + 1):
        games = build_season(year, data)
        write_season(year, games)

if __name__ == "__main__":
    main()
