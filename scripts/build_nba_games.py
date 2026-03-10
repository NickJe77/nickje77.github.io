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

    if pd.isna(g["gamedatetimeest"]):
        continue

    date = pd.to_datetime(g["gamedatetimeest"])

    season = date.year
    if date.month >= 10:
        season += 1

    game_id = str(g["gameid"])

    # skip preseason
    if game_id.startswith("001"):
        continue

    # determine game type
    if game_id.startswith("002"):
        game_type = "Regular Season"
    elif game_id.startswith("004"):
        game_type = "Playoffs"
    else:
        game_type = "Other"

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
            "player": p.get("name",""),
            "team": p.get("teamname",""),
            "minutes": p.get("minutes",""),
            "points": int(p.get("points",0) or 0),
            "rebounds": int(p.get("rebounds",0) or 0),
            "assists": int(p.get("assists",0) or 0),
            "steals": int(p.get("steals",0) or 0),
            "blocks": int(p.get("blocks",0) or 0),
            "turnovers": int(p.get("turnovers",0) or 0)
        })

    game_data = {
        "game_id": game_id,
        "date": str(date),
        "home_team": home,
        "away_team": away,
        "home_score": home_score,
        "away_score": away_score,
        "winner": winner,
        "arena": arena,
        "game_type": game_type,
        "players": plist
    }

    with open(file_path, "w") as f:
        json.dump(game_data, f, indent=2)

    # -------- update index.json --------

    index_path = season_dir / "index.json"

    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {"games": []}

    if game_id not in index["games"]:
        index["games"].append(game_id)

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    # -------- update games.json --------

    games_path = season_dir / "games.json"

    if games_path.exists():
        with open(games_path) as f:
            games_list = json.load(f)
    else:
        games_list = []

    games_list.append({
        "game_id": game_id,
        "date": str(date),
        "home_team": home,
        "away_team": away,
        "home_score": home_score,
        "away_score": away_score,
        "game_type": game_type
    })

    with open(games_path, "w") as f:
        json.dump(games_list, f, indent=2)

    written += 1


print("New games written:", written)
print("Existing games skipped:", skipped)
