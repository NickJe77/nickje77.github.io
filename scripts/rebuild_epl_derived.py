import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"

print("SCANNING RED CARD EVENTS")

player_totals = defaultdict(int)

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

        home = str(game.get("home_team", "")).strip()
        away = str(game.get("away_team", "")).strip()

        date = str(
            game.get("date")
            or game.get("match_date")
            or ""
        ).strip()

        seen_in_match = set()

        for red in game.get("red_cards", []):

            if not isinstance(red, dict):
                continue

            player = str(
                red.get("player")
                or ""
            ).strip()

            team = str(
                red.get("team")
                or ""
            ).strip()

            minute = str(
                red.get("minute")
                or ""
            ).strip()

            description = str(
                red.get("description")
                or red.get("detail")
                or red.get("type")
                or ""
            ).strip()

            if not player:
                continue

            key = (
                f"{player}|"
                f"{team}"
            )

            # SHOW DUPLICATE REDS INSIDE SAME MATCH

            if key in seen_in_match:

                print("\n===================================")
                print("DUPLICATE RED IN MATCH")
                print("FILE:", path)
                print("DATE:", date)
                print("MATCH:", home, "vs", away)
                print("PLAYER:", player)
                print("TEAM:", team)
                print("MINUTE:", minute)
                print("DESC:", description)

            seen_in_match.add(key)

        # NORMAL TOTALS

        counted = set()

        for red in game.get("red_cards", []):

            if not isinstance(red, dict):
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
                continue

            key = f"{player}|{team}"

            if key in counted:
                continue

            counted.add(key)

            player_totals[player] += 1

print("\n===================================")
print("TOP RED CARD TOTALS")
print("===================================")

for player, total in sorted(
    player_totals.items(),
    key=lambda x: -x[1]
)[:50]:

    print(player, "-", total)

print("\nDONE")
