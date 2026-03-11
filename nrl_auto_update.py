import json
from pathlib import Path

INDEX = Path("docs/data/nrl/index.json")
MATCH_DIR = Path("docs/data/nrl/matches/2026")

new_game = {
    "game_id": "2026R02G01",
    "date": "2026-03-15",
    "round": 2,
    "venue": "Suncorp Stadium",
    "home_team": "Brisbane Broncos",
    "away_team": "North Queensland Cowboys",
    "home_score": 24,
    "away_score": 18,
    "players": []
}

game_id = new_game["game_id"]

match_file = MATCH_DIR / f"{game_id}.json"

if not match_file.exists():

    MATCH_DIR.mkdir(parents=True, exist_ok=True)

    with open(match_file,"w") as f:
        json.dump(new_game,f,indent=2)

    with open(INDEX) as f:
        index=json.load(f)

    if game_id not in index["games"]:
        index["games"].append(game_id)

    with open(INDEX,"w") as f:
        json.dump(index,f,indent=2)

    print("Game added")

else:
    print("Game already exists")
