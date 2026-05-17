import os
import json

MATCHES_DIR = "docs/data/epl/matches"

print("FIXING EPL RED CARD EVENTS")

fixed_matches = 0
removed_events = 0

# =====================================================
# VALID / INVALID WORDS
# =====================================================

VALID_RED_WORDS = [
    "red",
    "sent off",
    "dismissed"
]

INVALID_RED_WORDS = [
    "yellow",
    "booking",
    "booked",
    "foul",
    "penalty",
    "goal",
    "substitution",
    "offside"
]

# =====================================================
# FILES
# =====================================================

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

        original_reds = game.get("red_cards", [])

        if not isinstance(original_reds, list):
            continue

        cleaned_reds = []

        seen = set()

        for red in original_reds:

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

            minute = str(
                red.get("minute")
                or ""
            ).strip()

            desc = str(
                red.get("description")
                or red.get("detail")
                or red.get("type")
                or ""
            ).lower().strip()

            if not player:
                removed_events += 1
                continue

            # =================================================
            # ONE RED PER PLAYER PER MATCH
            # =================================================

            key = f"{player}|{team}"

            if key in seen:
                removed_events += 1
                continue

            # =================================================
            # EMPTY DESCRIPTIONS
            # =================================================

            # keep ONLY first empty entry

            if not desc:

                seen.add(key)

                cleaned_reds.append(red)

                continue

            # =================================================
            # INVALID WORDS
            # =================================================

            invalid = False

            for word in INVALID_RED_WORDS:

                if word in desc:
                    invalid = True
                    break

            if invalid:
                removed_events += 1
                continue

            # =================================================
            # MUST CONTAIN RED WORDS
            # =================================================

            valid = False

            for word in VALID_RED_WORDS:

                if word in desc:
                    valid = True
                    break

            if not valid:
                removed_events += 1
                continue

            seen.add(key)

            cleaned_reds.append(red)

        # =================================================
        # SAVE FILE
        # =================================================

        game["red_cards"] = cleaned_reds

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
