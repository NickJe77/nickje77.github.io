#!/usr/bin/env python3

import pandas as pd
import json
from pathlib import Path

DATA = Path("data/kaggle_nba")
OUT = Path("docs/data/nba")

print("Loading CSV files...")

games = pd.read_csv(DATA / "Games.csv", low_memory=False)
players = pd.read_csv(DATA / "PlayerStatistics.csv", low_memory=False)

games.columns = games.columns.str.lower()
players.columns = players.columns.str.lower()

games["gamedatetimeest"] = pd.to_datetime(games["gamedatetimeest"], errors="coerce")

OUT.mkdir(parents=True, exist_ok=True)

def safe(v):
    if pd.isna(v):
        return 0
    return int(v)

seasons = {}

for _, g in games.iterrows():

    if pd.isna(g["gamedatetimeest"]):
        continue

    season = safe(g.get("season"))

    if season < 1976:
        continue

    game_id = str(g["gameid"])

    home = f"{g['hometeamcity']} {g['hometeamname']}"
    away = f"{g['awayteamcity']} {g['awayteamname']}"

    home_score = safe(g.get("homescore"))
    away_score = safe(g.get("awayscore"))

    arena = g.get("arenaname","")

    game_type = g.get("gametype","Regular Season")

    game_players = players[players["gameid"] == g["gameid"]]

    plist = []

    for _, p in game_players.iterrows():

        plist.append({
            "player_id": safe(p.get("personid")),
            "team_id": safe(p.get("teamid")),
            "minutes": p.get("minutes",""),
            "points": safe(p.get("points")),
            "rebounds": safe(p.get("rebounds")),
            "assists": safe(p.get("assists")),
            "steals": safe(p.get("steals")),
            "blocks": safe(p.get("blocks")),
            "turnovers": safe(p.get("turnovers")),
            "fgm": safe(p.get("fgm")),
            "fga": safe(p.get("fga")),
            "tpm": safe(p.get("tpm")),
            "tpa": safe(p.get("tpa")),
            "ftm": safe(p.get("ftm")),
            "fta": safe(p.get("fta"))
        })

    game = {
        "game_id": game_id,
        "date": str(g["gamedatetimeest"].date()),
        "season": season,
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

    seasons[season].append(game)

print("Writing season files...")

for season, games in seasons.items():

    path = OUT / f"{season}.json"

    with open(path,"w") as f:

        json.dump({
            "season": season,
            "games": games
        }, f, indent=2)

    print("Saved",season,"(",len(games),"games )")

print("Done.")
