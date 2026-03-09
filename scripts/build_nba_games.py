#!/usr/bin/env python3

import pandas as pd
import json
from pathlib import Path

DATA = Path("data/kaggle_nba")
OUT = Path("docs/data/nba")

games = pd.read_csv(DATA / "Game.csv", low_memory=False)
players = pd.read_csv(DATA / "GamePlayerStats.csv", low_memory=False)

games.columns = games.columns.str.lower()
players.columns = players.columns.str.lower()

written = 0
skipped = 0

for _, g in games.iterrows():

```
if pd.isna(g["gamedatetimeest"]):
    continue

date = pd.to_datetime(g["gamedatetimeest"])

if date < pd.Timestamp("2026-02-15"):
    continue

season = date.year
if date.month >= 10:
    season += 1

game_id = str(g["gameid"])

season_dir = OUT / str(season)
season_dir.mkdir(parents=True, exist_ok=True)

file_path = season_dir / f"{game_id}.json"

if file_path.exists():
    skipped += 1
    continue

home = f"{g['hometeamcity']} {g['hometeamname']}"
away = f"{g['awayteamcity']} {g['awayteamname']}"

home_score = int(g.get("homescore", 0) or 0)
away_score = int(g.get("awayscore", 0) or 0)

winner = home if home_score > away_score else away

arena = g.get("arenaname", "")

game_players = players[players["gameid"] == g["gameid"]]

plist = []

for _, p in game_players.iterrows():

    plist.append({
```
