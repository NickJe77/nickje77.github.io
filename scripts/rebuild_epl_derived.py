import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"

player_reds = defaultdict(list)

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

        reds = game.get("red_cards", [])

        for red in reds:

            if not isinstance(red, dict):
                continue

            player = str(red.get("player", "")).strip()

            if not player:
                continue

            player_reds[player].append(path)

# SHOW CRAZY TOTALS

for player, matches in sorted(
    player_reds.items(),
    key=lambda x: -len(x[1])
):

    if len(matches) > 10:

        print("\n================================================")
        print(player, len(matches))
        print("================================================")

        for m in matches[:50]:
            print(m)
