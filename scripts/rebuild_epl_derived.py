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

        url = str(game.get("url", "")).strip()

        if not url:
            continue

        if url in seen:

            print("DELETING DUPLICATE:")
            print(path)

            os.remove(path)

            deleted += 1

        else:

            seen[url] = path

print("\nTOTAL DELETED:", deleted)
print("TOTAL UNIQUE:", len(seen))
