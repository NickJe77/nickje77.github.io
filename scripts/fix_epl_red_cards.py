import os
import json
import shutil

MATCHES_DIR = "docs/data/epl/matches"

BACKUP_DIR = "docs/data/epl/red_card_backups"

os.makedirs(BACKUP_DIR, exist_ok=True)

print("FIXING EPL RED CARDS")

# =====================================================
# KNOWN EPL MAXIMUMS
# =====================================================

MAX_REDS = {
    "Duncan Ferguson": 8,
    "Patrick Vieira": 8,
    "Richard Dunne": 8,
    "Roy Keane": 7,
    "Vinnie Jones": 7,
    "Alan Smith": 8,
    "Lee Cattermole": 7
}

career_reds = {}

fixed_files = 0
removed_events = 0

# =====================================================
# HELPERS
# =====================================================

def clean(v):
    return str(v or "").strip()

# =====================================================
# PROCESS FILES
# =====================================================

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

        yellows = game.get("yellow_cards", [])

        cleaned_reds = []

        changed = False

        seen = set()

        for red in reds:

            if not isinstance(red, dict):
                changed = True
                removed_events += 1
                continue

            player = clean(red.get("player"))
            minute_raw = clean(red.get("minute"))
            team = clean(red.get("team"))

            if not player or not team:
                changed = True
                removed_events += 1
                continue

            # =========================================
            # CLEAN MINUTE
            # =========================================

            digits = ""

            for c in minute_raw:

                if c.isdigit():
                    digits += c

            try:
                minute = int(digits)
            except:
                minute = 90

            # =========================================
            # REMOVE IMPOSSIBLE MINUTES
            # =========================================

            if minute <= 1:
                changed = True
                removed_events += 1
                continue

            # =========================================
            # REMOVE DUPLICATES
            # =========================================

            key = f"{player}|{team}|{minute}"

            if key in seen:
                changed = True
                removed_events += 1
                continue

            seen.add(key)

            # =========================================
            # REMOVE REDS THAT MATCH YELLOW EVENTS
            # =========================================

            yellow_match = False

            for y in yellows:

                if not isinstance(y, dict):
                    continue

                yp = clean(y.get("player"))
                ym = clean(y.get("minute"))

                if yp == player and ym == minute_raw:
                    yellow_match = True
                    break

            if yellow_match:
                changed = True
                removed_events += 1
                continue

            # =========================================
            # CAREER LIMITS
            # =========================================

            career_reds.setdefault(player, 0)

            limit = MAX_REDS.get(player, 8)

            if career_reds[player] >= limit:
                changed = True
                removed_events += 1
                continue

            career_reds[player] += 1

            cleaned_reds.append(red)

        if changed:

            backup_path = os.path.join(
                BACKUP_DIR,
                file
            )

            shutil.copy2(path, backup_path)

            game["red_cards"] = cleaned_reds

            with open(path, "w", encoding="utf-8") as f:

                json.dump(
                    game,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            fixed_files += 1

print()
print("FILES FIXED:", fixed_files)
print("EVENTS REMOVED:", removed_events)
print("DONE")
