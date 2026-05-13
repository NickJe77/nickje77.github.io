import os
import json

NBA_DIR = "docs/data/nba/2025"
GAMES_FILE = os.path.join(NBA_DIR, "games.json")

print("BUILDING CLEAN 2025 GAMES FILE")

games = []

for filename in sorted(os.listdir(NBA_DIR)):

    if not filename.endswith(".json"):
        continue

    if filename in ["games.json", "index.json"]:
        continue

    path = os.path.join(NBA_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except Exception:

        print(f"BAD JSON {filename}")
        continue

    if isinstance(game, list):
        continue

    if not isinstance(game, dict):
        continue

    game_id = str(game.get("game_id", ""))

    if not game_id:
        continue

    # ==========================================
    # KEEP ONLY 2025/26 SEASON IDS
    # ==========================================

    if not (
        game_id.startswith("00225")
        or game_id.startswith("00425")
    ):
        continue

    games.append(game)

# SORT BY DATE
games.sort(
    key=lambda x: x.get("date", ""),
    reverse=True
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

print(f"BUILT {len(games)} GAMES")
print("DONE")
