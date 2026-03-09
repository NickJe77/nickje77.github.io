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
            "player_id": int(p["personid"]),
            "team_id": int(p["teamid"]),
            "minutes": p.get("minutes", ""),
            "points": int(p.get("points", 0) or 0),
            "rebounds": int(p.get("rebounds", 0) or 0),
            "assists": int(p.get("assists", 0) or 0),
            "steals": int(p.get("steals", 0) or 0),
            "blocks": int(p.get("blocks", 0) or 0),
            "turnovers": int(p.get("turnovers", 0) or 0),
            "fgm": int(p.get("fgm", 0) or 0),
            "fga": int(p.get("fga", 0) or 0),
            "tpm": int(p.get("tpm", 0) or 0),
            "tpa": int(p.get("tpa", 0) or 0),
            "ftm": int(p.get("ftm", 0) or 0),
            "fta": int(p.get("fta", 0) or 0)
        })

    with open(file_path, "w") as f:
        json.dump({
            "game_id": game_id,
            "season": season,
            "date": str(date.date()),
            "home_team": home,
            "away_team": away,
            "home_score": home_score,
            "away_score": away_score,
            "winner": winner,
            "arena": arena,
            "players": plist
        }, f, indent=2)

    written += 1

print("New games written:", written)
print("Existing games skipped:", skipped)
