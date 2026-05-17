import os
import json

MATCHES_DIR = "docs/data/epl/matches"

print("FIXING EPL RED CARD EVENTS")

fixed_matches = 0
removed_events = 0

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in sorted(files):

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

        cleaned = []
        seen = set()

        for red in reds:

            if not isinstance(red, dict):
                removed_events += 1
                continue

            player = str(
                red.get("player")
                or ""
            ).strip()

            team = str(
                red.get("team")
                or ""
            ).strip()

            if not player:
                removed_events += 1
                continue

            # =================================================
            # ONLY ONE RED PER PLAYER PER MATCH
            # =================================================

            key = f"{player}|{team}"

            if key in seen:
                removed_events += 1
                continue

            seen.add(key)

            cleaned.append({
                "player": player,
                "team": team,
                "minute": red.get("minute", "")
            })

        game["red_cards"] = cleaned

        with open(path, "w", encoding="utf-8") as f:

            json.dump(
                game,
                f,
                indent=2,
                ensure_ascii=False
            )

        fixed_matches += 1

print("MATCHES FIXED:", fixed_matches)
print("RED EVENTS REMOVED:", removed_events)
print("DONE")
