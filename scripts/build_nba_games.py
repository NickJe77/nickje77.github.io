#!/usr/bin/env python3

import pandas as pd
import json
from pathlib import Path

DATA = Path("data/kaggle_nba")
OUT = Path("docs/data/nba")

games = pd.read_csv(DATA / "Games.csv", low_memory=False)
players = pd.read_csv(DATA / "PlayerStatistics.csv", low_memory=False)

games.columns = games.columns.str.lower()
players.columns = players.columns.str.lower()

games["gamedatetimeest"] = pd.to_datetime(games["gamedatetimeest"], errors="coerce")

def safe_int(v):
    if pd.isna(v):
        return 0
    return int(v)

seasons = {}

for _, g in games.iterrows():

    if pd.isna(g["gamedatetimeest"]):
        continue

    date = g["gamedatetimeest"]

    season = date.year
    if date.month >= 10:
        season += 1

    if season < 1976:
        continue

    game_id = str(g["gameid"])

    home = f"{g['hometeamcity']} {g['hometeamname']}"
    away = f"{g['awayteamcity']} {g['awayteamname']}"

    home_score = safe_int(g.get("homescore"))
    away_score = safe_int(g.get("awayscore"))

    arena = g.get("arenaname", "")

    game_type = g.get("gametype", "Regular Season")

    game_players = players[players["gameid"] == g["gameid"]]

    plist = []

    for _, p in game_players.iterrows():

        plist.append({
            "player_id": safe_int(p.get("personid")),
            "team_id": safe_int(p.get("teamid")),
            "minutes": p.get("minutes",""),
            "points": safe_int(p.get("points")),
            "rebounds": safe_int(p.get("rebounds")),
            "assists": safe_int(p.get("assists")),
            "steals": safe_int(p.get("steals")),
            "blocks": safe_int(p.get("blocks")),
            "turnovers": safe_int(p.get("turnovers")),
            "fgm": safe_int(p.get("fgm")),
            "fga": safe_int(p.get("fga")),
            "tpm": safe_int(p.get("tpm")),
            "tpa": safe_int(p.get("tpa")),
            "ftm": safe_int(p.get("ftm")),
            "fta": safe_int(p.get("fta"))
        })

    game_obj = {
        "game_id": game_id,
        "date": str(date.date()),
        "game_type": game_type,
        "home_team": home,
        "away_team": away,
        "home_score": home_score,
        "away_score": away_score,
        "arena": arena,
        "players": plist
    }

    if season not in seasons:
        seasons[season] = []

    seasons[season].append(game_obj)

OUT.mkdir(parents=True, exist_ok=True)

for season, games_list in seasons.items():

    file_path = OUT / f"{season}.json"

    with open(file_path, "w") as f:

        json.dump({
            "season": season,
            "games": games_list
        }, f, indent=2)

print("Seasons written:", len(seasons))
