import os
import json

NBA_DIR = "docs/data/nba/2025"
INDEX_FILE = os.path.join(NBA_DIR, "index.json")

print("BUILDING NBA INDEX")

game_ids = []

for filename in sorted(os.listdir(NBA_DIR)):

    if not filename.endswith(".json"):
        continue

    if filename == "index.json":
        continue

    path = os.path.join(NBA_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except Exception:

        print(f"BAD JSON {filename}")
        continue

    # SKIP ARRAYS
    if isinstance(game, list):
        continue

    if not isinstance(game, dict):
        continue

    game_id = game.get("game_id")

    if not game_id:
        continue

    game_ids.append(game_id)

# REMOVE DUPLICATES
game_ids = list(dict.fromkeys(game_ids))

# SORT
game_ids.sort()

output = {
    "games": game_ids
}

with open(
    INDEX_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        indent=2
    )

print(f"BUILT {len(game_ids)} GAMES")
print("DONE")
