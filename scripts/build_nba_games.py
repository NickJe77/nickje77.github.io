#!/usr/bin/env python3

import pandas as pd
import json
from pathlib import Path

DATA = Path("data/kaggle_nba")
OUT = Path("docs/data/nba")

games_file = DATA / "Games.csv"

games = pd.read_csv(games_file, low_memory=False)

games.columns = games.columns.str.lower()

print("Games columns:", list(games.columns))

written = 0

for _, g in games.iterrows():

    if pd.isna(g["gamedatetimeest"]):
        continue

    date = pd.to_datetime(g["gamedatetimeest"])

    # ONLY games from Feb 15 2026 onwards
    if date < pd.Timestamp("2026-02-15"):
        continue

    season = date.year
    if date.month >= 10:
        season += 1

    game_id = str(g["gameid"])

    home = f"{g['hometeamcity']} {g['hometeamname']}"
    away = f"{g['awayteamcity']} {g['awayteamname']}"

    home_score = int(g["homescore"])
    away_score = int(g["awayscore"])

    winner = home if home_score > away_score else away

    arena = g.get("arenaname","")

    season_dir = OUT / str(season)
    season_dir.mkdir(parents=True, exist_ok=True)

    with open(season_dir / f"{game_id}.json","w") as f:

        json.dump({
            "game_id": game_id,
            "season": season,
            "date": str(date.date()),
            "home_team": home,
            "away_team": away,
            "home_score": home_score,
            "away_score": away_score,
            "winner": winner,
            "arena": arena
        }, f, indent=2)

    written += 1

print("Games written:", written)
