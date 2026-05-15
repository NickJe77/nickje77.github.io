import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"

player_matches = defaultdict(list)

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

        reds = game.get("red_cards", [])

        for red in reds:

            if not isinstance(red, dict):
                continue

            player = str(
                red.get("player", "")
            ).strip()

            if player != "Freddie Ljungberg":
                continue

            print("\n====================================")
            print(path)
            print(json.dumps(red, indent=2))
            print("====================================")
