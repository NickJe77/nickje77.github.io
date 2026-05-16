import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"

red_totals = defaultdict(int)

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

        if not isinstance(reds, list):
            continue

        for red in reds:

            if not isinstance(red, dict):
                continue

            player = str(
                red.get("player", "")
            ).strip()

            if not player:
                continue

            red_totals[player] += 1

print("\nTOP RED CARD TOTALS\n")

for player, reds in sorted(
    red_totals.items(),
    key=lambda x: -x[1]
)[:100]:

    print(player, reds)
