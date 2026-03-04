#!/usr/bin/env python3

import pandas as pd
import json
from pathlib import Path

DATA = Path("data/kaggle_nba")
OUT = Path("docs/data/nba")

games = pd.read_csv(DATA / "Games.csv", low_memory=False)
players = pd.read_csv(DATA / "Players.csv", low_memory=False)

games.columns = games.columns.str.lower()
players.columns = players.columns.str.lower()

count = 0

for _, g in games.iterrows():

    game_id = str(g["gameid"])
    season = int(g["season"])

    if season < 1976:
        continue

    home = g["hometeam"]
    away = g["awayteam"]

    home_score = int(g["homescore"])
    away_score = int(g["awayscore"])

    winner = home if home_score > away_score else away

    date = g["date"]

    game_players = players[players["gameid"] == g["gameid"]]

    plist = []

    for _, p in game_players.iterrows():
        plist.append({
            "player_name": p["player"],
            "team": p["team"],
            "points": int(p["points"]),
            "rebounds": int(p["rebounds"]),
            "assists": int(p["assists"])
        })

    season_dir = OUT / str(season)
    season_dir.mkdir(parents=True, exist_ok=True)

    with open(season_dir / f"{game_id}.json","w") as f:

        json.dump({
            "game_id": game_id,
            "season": season,
            "date": date,
            "home_team": home,
            "away_team": away,
            "home_score": home_score,
            "away_score": away_score,
            "winner": winner,
            "players": plist
        }, f, indent=2)

    count += 1

print("Games written:", count)
