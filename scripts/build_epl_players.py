import os
import json

MATCHES_DIR = "docs/data/epl/matches"

print("REMOVING CORRUPTED CARD DATA")

updated = 0

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in files:

        if not file.endswith(".json"):
            continue

        path = os.path.join(root, file)

        try:
            with open(path, "r", encoding="utf-8") as f:
                game = json.load(f)
        except Exception:
            continue

        changed = False

        # WIPE BAD DATA

        if "yellow_cards" in game:
            game["yellow_cards"] = []
            changed = True

        if "red_cards" in game:
            game["red_cards"] = []
            changed = True

        if changed:

            with open(path, "w", encoding="utf-8") as f:
                json.dump(game, f, indent=2)

            updated += 1

print(f"UPDATED: {updated}")
print("DONE")
