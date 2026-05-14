import os
import json
import re

MATCHES_DIR = "docs/data/epl/matches"

print("FIXING EPL CARD DATA")

def clean(v):
    return str(v or "").strip()

def extract_player_name(entry):

    # already structured
    if isinstance(entry, dict):

        return clean(
            entry.get("player")
            or entry.get("name")
        )

    text = clean(entry)

    # remove minutes
    text = re.sub(r"\(\d+\)", "", text)

    # remove card text
    text = re.sub(
        r"yellow card|red card|second yellow",
        "",
        text,
        flags=re.I
    )

    # remove commas/numbers
    text = re.sub(r"[\d']", "", text)

    return text.strip()

fixed_files = 0

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

        # -----------------------------
        # FIX YELLOWS
        # -----------------------------

        clean_yellows = []

        for y in game.get("yellow_cards", []):

            player = extract_player_name(y)

            if not player:
                continue

            if isinstance(y, dict):

                team = clean(y.get("team"))

            else:
                team = ""

            clean_yellows.append({
                "player": player,
                "team": team
            })

        if clean_yellows:
            game["yellow_cards"] = clean_yellows
            changed = True

        # -----------------------------
        # FIX REDS
        # -----------------------------

        clean_reds = []

        for r in game.get("red_cards", []):

            player = extract_player_name(r)

            if not player:
                continue

            if isinstance(r, dict):

                team = clean(r.get("team"))

            else:
                team = ""

            clean_reds.append({
                "player": player,
                "team": team
            })

        if clean_reds:
            game["red_cards"] = clean_reds
            changed = True

        # -----------------------------
        # DEDUPE REDS
        # -----------------------------

        seen = set()
        deduped_reds = []

        for r in game.get("red_cards", []):

            key = (
                clean(r.get("player")).lower(),
                clean(r.get("team")).lower()
            )

            if key in seen:
                continue

            seen.add(key)
            deduped_reds.append(r)

        game["red_cards"] = deduped_reds

        # -----------------------------
        # SAVE
        # -----------------------------

        if changed:

            with open(path, "w", encoding="utf-8") as f:
                json.dump(game, f, indent=2)

            fixed_files += 1

print(f"FIXED FILES: {fixed_files}")
print("DONE")
