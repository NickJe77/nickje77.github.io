import pandas as pd
import json
import os

DATA_PATH = "data"

# find dataset folder automatically
dataset_folder = None
for f in os.listdir(DATA_PATH):
    if os.path.isdir(os.path.join(DATA_PATH, f)):
        dataset_folder = os.path.join(DATA_PATH, f)
        break

if dataset_folder is None:
    raise Exception("Dataset folder not found")

box_file = os.path.join(dataset_folder, "player_box_score.csv")
game_file = os.path.join(dataset_folder, "game.csv")

print("Loading:", box_file)
print("Loading:", game_file)

box = pd.read_csv(box_file)
games = pd.read_csv(game_file)

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

        player = {
            "player": r["player_name"],
            "team": r["team_abbreviation"],
            "minutes": r["min"],
            "points": r["pts"],
            "rebounds": r["reb"],
            "assists": r["ast"]
        }

        game["players"].append(player)

    season = str(game["season"])

    if season not in output:
        output[season] = []

    output[season].append(game)

BASE = "docs/data/nba/seasons"
os.makedirs(BASE, exist_ok=True)

for season, games in output.items():

    with open(f"{BASE}/{season}.json", "w") as f:
        json.dump(games, f)

print("NBA files created")
