import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"

seen = defaultdict(list)

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

        seen[url].append(path)

duplicates = 0

for url, paths in seen.items():

    if len(paths) > 1:

        duplicates += 1

        print("\n====================================")
        print(url)
        print("COPIES:", len(paths))

        for p in paths[:20]:
            print(p)

print("\nTOTAL DUPLICATED MATCHES:", duplicates)
