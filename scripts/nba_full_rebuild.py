import os
import json

NBA_DIR = "docs/data/nba/2025"
INDEX_FILE = os.path.join(NBA_DIR, "index.json")

print("BUILDING NBA INDEX")

games = []

for filename in sorted(os.listdir(NBA_DIR)):

    if not filename.endswith(".json"):
        continue

    if filename == "index.json":
        continue

    path = os.path.join(NBA_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except Exception as e:

        print(f"BAD FILE {filename}")
        continue

    game_id = game.get("game_id", "")

    if not game_id:
        continue

    games.append({

        "game_id": game_id,

        "date":
            game.get("date", ""),

        "game_type":
            game.get("game_type", ""),

        "home_team":
            game.get("home_team", ""),

        "away_team":
            game.get("away_team", ""),

        "home_score":
            game.get("home_score", 0),

        "away_score":
            game.get("away_score", 0),

        "arena":
            game.get("arena", ""),

        "file":
            filename
    })

# SORT NEWEST FIRST
games.sort(
    key=lambda x: x.get("date", ""),
    reverse=True
)

with open(
    INDEX_FILE,
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
