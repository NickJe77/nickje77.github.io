import os
import json

SEASON_DIR = "docs/data/nba/2025"
GAMES_FILE = os.path.join(SEASON_DIR, "games.json")

print("FIXING NBA CURRENT SEASON")

games = []

for filename in os.listdir(SEASON_DIR):

    if not filename.endswith(".json"):
        continue

    if filename in ["games.json", "index.json"]:
        continue

    # KEEP ONLY CURRENT SEASON IDS
    if not (
        filename.startswith("00225")
        or filename.startswith("00425")
    ):
        print(f"SKIPPING {filename}")
        continue

    path = os.path.join(SEASON_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except:
        continue

    if not isinstance(game, dict):
        continue

    if not game.get("home_team"):
        continue

    games.append(game)

games.sort(
    key=lambda x: x.get("date", "")
)

with open(
    GAMES_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        games,
        f,
        indent=2
    )

print(f"BUILT {len(games)} CLEAN GAMES")
print("DONE")
