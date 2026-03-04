#!/usr/bin/env python3

import pandas as pd
import json
from pathlib import Path

DATA = Path("data/kaggle_nba")
OUT = Path("docs/data/nba")

csvs = list(DATA.rglob("*.csv"))

if not csvs:
    raise Exception("No CSV files found in dataset")

games_file = None
players_file = None

for f in csvs:
    n = f.name.lower()
    if "game" in n:
        games_file = f
    if "player" in n or "box" in n:
        players_file = f

if games_file is None or players_file is None:
    raise Exception("Could not locate games or player csv")

print("Using:", games_file)
print("Using:", players_file)

games = pd.read_csv(games_file)
players = pd.read_csv(players_file)

games.columns = games.columns.str.lower()
players.columns = players.columns.str.lower()

for _, g in games.iterrows():

    game_id = str(g.get("game_id") or g.get("gameid"))
    if not game_id:
        continue

    season = int(g.get("season",0))
    if season < 1976:
        continue

    date = str(g.get("game_date") or g.get("date") or "")

    home = g.get("home_team") or g.get("home_team_name")
    away = g.get("visitor_team_name") or g.get("away_team")

    home_score = int(g.get("pts_home",0))
    away_score = int(g.get("pts_away",0))

    winner = home if home_score > away_score else away

    p = players[players["game_id"] == int(game_id)]

    plist = []

    for _, row in p.iterrows():
        plist.append({
            "player_id": str(row.get("player_id","")),
            "player_name": row.get("player_name",""),
            "team": row.get("team_abbreviation",""),
            "points": int(row.get("pts",0)),
            "rebounds": int(row.get("reb",0)),
            "assists": int(row.get("ast",0))
        })

    season_dir = OUT / str(season)
    season_dir.mkdir(parents=True, exist_ok=True)

    game_json = {
        "game_id": game_id,
        "season": season,
        "date": date,
        "home_team": home,
        "away_team": away,
        "home_score": home_score,
        "away_score": away_score,
        "winner": winner,
        "players": plist
    }

    with open(season_dir / f"{game_id}.json","w") as f:
        json.dump(game_json,f,indent=2)

print("NBA rebuild complete")
