import pandas as pd
import json
import os

# Kaggle dataset folder
DATA_PATH = "data/historical-nba-data-and-player-box-scores"

box = pd.read_csv(f"{DATA_PATH}/player_box_score.csv")
games = pd.read_csv(f"{DATA_PATH}/game.csv")

merged = box.merge(games, on="game_id")

output = {}

for gid, g in merged.groupby("game_id"):

    meta = g.iloc[0]

    game = {
        "game_id": int(gid),
        "season": int(meta["season"]),
        "date": meta["game_date"],
        "home_team": meta["home_team"],
        "away_team": meta["away_team"],
        "home_score": int(meta["home_pts"]),
        "away_score": int(meta["away_pts"]),
        "winner": meta["home_team"] if meta["home_pts"] > meta["away_pts"] else meta["away_team"],
        "players": []
    }

    for _, r in g.iterrows():

        player = {
            "player": r["player_name"],
            "team": r["team_abbreviation"],
            "minutes": r["min"],
            "points": int(r["pts"]) if not pd.isna(r["pts"]) else 0,
            "rebounds": int(r["reb"]) if not pd.isna(r["reb"]) else 0,
            "assists": int(r["ast"]) if not pd.isna(r["ast"]) else 0,
            "steals": int(r["stl"]) if not pd.isna(r["stl"]) else 0,
            "blocks": int(r["blk"]) if not pd.isna(r["blk"]) else 0,
            "turnovers": int(r["tov"]) if not pd.isna(r["tov"]) else 0
        }

        game["players"].append(player)

    season = str(game["season"])

    if season not in output:
        output[season] = []

    output[season].append(game)

# Output folder used by your website
BASE = "docs/data/nba/seasons"

os.makedirs(BASE, exist_ok=True)

for season, games in output.items():

    with open(f"{BASE}/{season}.json", "w") as f:
        json.dump(games, f)

print("NBA season files built successfully")
