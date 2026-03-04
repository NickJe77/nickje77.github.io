#!/usr/bin/env python3

import pandas as pd
import json
from pathlib import Path

DATA = Path("data/kaggle_nba")
OUT = Path("docs/data/nba")

games_file = DATA / "Games.csv"
players_file = DATA / "Players.csv"

games = pd.read_csv(games_file, low_memory=False)
players = pd.read_csv(players_file, low_memory=False)

games.columns = games.columns.str.lower()
players.columns = players.columns.str.lower()

print("Games columns:", list(games.columns))
print("Players columns:", list(players.columns))

def find_col(cols, options):
    for o in options:
        if o in cols:
            return o
    return None

gid = find_col(games.columns, ["gameid","game_id","id"])
date_col = find_col(games.columns, ["date","gamedate"])
home_col = find_col(games.columns, ["hometeam","home_team"])
away_col = find_col(games.columns, ["awayteam","away_team"])
hs_col = find_col(games.columns, ["homescore","home_score","pts_home"])
as_col = find_col(games.columns, ["awayscore","away_score","pts_away"])

pgid = find_col(players.columns, ["gameid","game_id"])
pname = find_col(players.columns, ["player","player_name"])
pteam = find_col(players.columns, ["team","team_name"])
ppts = find_col(players.columns, ["points","pts"])
preb = find_col(players.columns, ["rebounds","reb"])
past = find_col(players.columns, ["assists","ast"])

written = 0

for _, g in games.iterrows():

    date = pd.to_datetime(g[date_col])
    season = date.year
    if date.month >= 10:
        season += 1

    if season < 1976:
        continue

    game_id = str(g[gid])

    home = g[home_col]
    away = g[away_col]

    home_score = int(g[hs_col])
    away_score = int(g[as_col])

    winner = home if home_score > away_score else away

    gp = players[players[pgid] == g[gid]]

    plist = []

    for _, p in gp.iterrows():

        plist.append({
            "player_name": p[pname],
            "team": p[pteam],
            "points": int(p[ppts]),
            "rebounds": int(p[preb]),
            "assists": int(p[past])
        })

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
            "players": plist
        }, f, indent=2)

    written += 1

print("Games written:", written)
