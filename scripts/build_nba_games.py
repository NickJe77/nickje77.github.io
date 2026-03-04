#!/usr/bin/env python3

import pandas as pd
import json
from pathlib import Path

DATASET_DIR = Path("data/kaggle_nba")
OUTPUT_DIR = Path("docs/data/nba")

# find csv files automatically
csv_files = list(DATASET_DIR.rglob("*.csv"))

if not csv_files:
    raise Exception("No CSV files found")

games_csv = None
players_csv = None

for f in csv_files:
    name = f.name.lower()
    if "game" in name:
        games_csv = f
    if "player" in name or "box" in name:
        players_csv = f

if not games_csv or not players_csv:
    raise Exception("Could not find game or player CSV")

print("Games file:", games_csv)
print("Players file:", players_csv)

games = pd.read_csv(games_csv)
players = pd.read_csv(players_csv)

games.columns = [c.lower() for c in games.columns]
players.columns = [c.lower() for c in players.columns]

for _, g in games.iterrows():

    game_id = str(g.get("game_id") or g.get("gameid"))
    if not game_id:
        continue

    date = str(g.get("game_date") or g.get("date") or "")

    season = int(g.get("season") or 0)

    if season < 1976:
        continue

    home = g.get("home_team") or g.get("home_team_name")
    away = g.get("away_team") or g.get("visitor_team_name")

    home_score = int(g.get("pts_home") or g.get("home_score") or 0)
    away_score = int(g.get("pts_away") or g.get("away_score") or 0)

    winner = home if home_score > away_score else away

    game_players = players[players["game_id"] == int(game_id)]

    plist = []

    for _, p in game_players.iterrows():
        plist.append({
            "player_id": str(p.get("player_id","")),
            "player_name": p.get("player_name",""),
            "team": p.get("team_abbreviation",""),
            "points": int(p.get("pts",0)),
            "rebounds": int(p.get("reb",0)),
            "assists": int(p.get("ast",0))
        })

    season_dir = OUTPUT_DIR / str(season)
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
