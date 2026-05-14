import os
import json
import re

MATCHES_DIR = "docs/data/epl/matches"

print("REBUILDING EPL CARD DATA")

def clean(v):
    return str(v or "").strip()

def parse_card_entry(entry):

    if isinstance(entry, dict):

        player = clean(
            entry.get("player")
            or entry.get("name")
        )

        team = clean(entry.get("team"))

        minute = clean(
            entry.get("minute")
        )

        return {
            "player": player,
            "team": team,
            "minute": minute
        }

    text = clean(entry)

    minute_match = re.search(r"(\d+)", text)

    minute = ""

    if minute_match:
        minute = minute_match.group(1)

    text = re.sub(r"\(\d+\)", "", text)

    text = re.sub(r"\d+", "", text)

    text = re.sub(
        r"yellow card|red card|second yellow",
        "",
        text,
        flags=re.I
    )

    text = text.strip(" -:,;'")

    return {
        "player": text.strip(),
        "team": "",
        "minute": minute
    }

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

        # -----------------------------------
        # REBUILD YELLOWS
        # -----------------------------------

        rebuilt_yellows = []
        yellow_seen = set()

        original_yellows = game.get("yellow_cards", [])

        if not isinstance(original_yellows, list):
            original_yellows = []

        for y in original_yellows:

            parsed = parse_card_entry(y)

            player = clean(parsed["player"])

            if not player:
                continue

            key = (
                player.lower(),
                parsed["minute"]
            )

            if key in yellow_seen:
                continue

            yellow_seen.add(key)

            rebuilt_yellows.append({
                "player": player,
                "team": parsed["team"],
                "minute": parsed["minute"]
            })

        # clamp max 2 yellows per player
        yellow_counts = {}

        final_yellows = []

        for y in rebuilt_yellows:

            player = y["player"]

            yellow_counts[player] = (
                yellow_counts.get(player, 0) + 1
            )

            if yellow_counts[player] <= 2:
                final_yellows.append(y)

        # -----------------------------------
        # REBUILD REDS
        # -----------------------------------

        rebuilt_reds = []
        red_seen = set()

        original_reds = game.get("red_cards", [])

        if not isinstance(original_reds, list):
            original_reds = []

        for r in original_reds:

            parsed = parse_card_entry(r)

            player = clean(parsed["player"])

            if not player:
                continue

            key = player.lower()

            # max 1 red per player
            if key in red_seen:
                continue

            red_seen.add(key)

            rebuilt_reds.append({
                "player": player,
                "team": parsed["team"],
                "minute": parsed["minute"]
            })

        game["yellow_cards"] = final_yellows
        game["red_cards"] = rebuilt_reds

        with open(path, "w", encoding="utf-8") as f:
            json.dump(game, f, indent=2)

        updated += 1

print(f"UPDATED MATCHES: {updated}")
print("DONE")
