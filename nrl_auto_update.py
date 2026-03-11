import json
from pathlib import Path

INDEX = Path("docs/data/nrl/index.json")
MATCH_DIR = Path("docs/data/nrl/matches/2026")

MATCH_DIR.mkdir(parents=True, exist_ok=True)

# collect all match files
games = []

for f in MATCH_DIR.glob("*.json"):
    games.append(f.stem)

games = sorted(games)

# build index
index = {
    "season": 2026,
    "games": games
}

with open(INDEX, "w") as f:
    json.dump(index, f, indent=2)

print("Indexed", len(games), "games")
