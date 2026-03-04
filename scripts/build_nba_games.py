import pandas as pd
import json
import os

box = pd.read_csv("data/player_box_scores.csv")
games = pd.read_csv("data/games.csv")

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
        "players": []
    }

    for _, r in g.iterrows():
        game["players"].append({
            "player": r["player_name"],
            "team": r["team"],
            "minutes": r["min"],
            "points": r["pts"],
            "rebounds": r["reb"],
            "assists": r["ast"],
            "steals": r["stl"],
            "blocks": r["blk"]
        })

    season = str(game["season"])

    if season not in output:
        output[season] = []

    output[season].append(game)

base = "docs/data/nba/seasons"

os.makedirs(base, exist_ok=True)

for season, games in output.items():

    with open(f"{base}/{season}.json", "w") as f:
        json.dump(games, f)
