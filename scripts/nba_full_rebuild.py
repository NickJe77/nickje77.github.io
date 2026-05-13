import os
import json

NBA_DIR = "docs/data/nba/2025"

# THIS IS THE FILE YOUR SITE IS MOST LIKELY USING
MASTER_FILE = "docs/data/nba/2025.json"

print("BUILDING NBA MASTER FILE")

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

    except Exception:

        print(f"BAD JSON {filename}")
        continue

    if isinstance(game, list):
        continue

    if not isinstance(game, dict):
        continue

    if not game.get("game_id"):
        continue

    games.append({

        "game_id":
            game.get("game_id", ""),

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

        # IMPORTANT
        "file":
            f"2025/{filename}"
    })

games.sort(
    key=lambda x: x.get("date", ""),
    reverse=True
)

with open(
    MASTER_FILE,
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
