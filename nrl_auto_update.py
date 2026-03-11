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

MATCH_DIR.mkdir(parents=True, exist_ok=True)

match_file = MATCH_DIR / f"{game_id}.json"

# ----------------------------
# CREATE MATCH FILE
# ----------------------------

if not match_file.exists():

    with open(match_file, "w") as f:
        json.dump(new_game, f, indent=2)

    print("Match file created")

else:
    print("Match already exists")


# ----------------------------
# LOAD INDEX
# ----------------------------

if INDEX.exists():

    try:
        with open(INDEX) as f:
            index = json.load(f)
    except:
        index = {}

else:
    index = {}

# ----------------------------
# ENSURE STRUCTURE
# ----------------------------

if "season" not in index:
    index["season"] = 2026

if "games" not in index:
    index["games"] = []

# ----------------------------
# ADD GAME
# ----------------------------

if game_id not in index["games"]:

    index["games"].append(game_id)

    # keep games sorted
    index["games"] = sorted(index["games"])

    print("Game added to index")

else:
    print("Game already in index")


# ----------------------------
# SAVE INDEX
# ----------------------------

with open(INDEX, "w") as f:
    json.dump(index, f, indent=2)

print("Update complete")
