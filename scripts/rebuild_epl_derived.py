import os
import json

MATCHES_DIR = "docs/data/epl/matches"

seen = {}
deleted = 0

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in files:

        if not file.endswith(".json"):
            continue

        path = os.path.join(root, file)

        try:

            with open(path, "r", encoding="utf-8") as f:
                game = json.load(f)

        except:
            continue

        if not isinstance(game, dict):
            continue

        key = (
            str(game.get("date", "")).strip(),
            str(game.get("home_team", "")).strip(),
            str(game.get("away_team", "")).strip(),
            str(game.get("home_score", "")).strip(),
            str(game.get("away_score", "")).strip()
        )

        if key in seen:

            print("DELETING:", path)

            os.remove(path)

            deleted += 1

        else:

            seen[key] = path

print("\nTOTAL DELETED:", deleted)
print("TOTAL UNIQUE MATCHES:", len(seen))
