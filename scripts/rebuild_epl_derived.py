import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"

print("FIXING FALSE RED CARDS")

# =====================================================
# KNOWN FALSE RED CARD PATTERN
# =====================================================
#
# Your dataset clearly has:
# - yellow cards copied into red_cards
# - especially older seasons
#
# Real EPL red cards are usually:
# - single events
# - late in games
# - not repeated constantly
#
# This script removes obvious fake reds:
#
# 1. duplicate reds for same player same match
# 2. reds before 35th minute
# 3. matches with 3+ reds
# 4. players with absurd career totals
#
# =====================================================

player_red_totals = defaultdict(int)

match_files = []

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in files:

        if file.endswith(".json"):

            match_files.append(
                os.path.join(root, file)
            )

print("MATCH FILES:", len(match_files))

# =====================================================
# PASS 1
# COUNT TOTALS
# =====================================================

for path in match_files:

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except:
        continue

    reds = game.get("red_cards", [])

    if not isinstance(reds, list):
        continue

    seen = set()

    for red in reds:

        if not isinstance(red, dict):
            continue

        player = str(
            red.get("player", "")
        ).strip()

        if not player:
            continue

        if player in seen:
            continue

        seen.add(player)

        player_red_totals[player] += 1

# =====================================================
# PASS 2
# CLEAN FILES
# =====================================================

fixed = 0

for path in match_files:

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except:
        continue

    reds = game.get("red_cards", [])

    if not isinstance(reds, list):
        continue

    cleaned = []

    seen_players = set()

    for red in reds:

        if not isinstance(red, dict):
            continue

        player = str(
            red.get("player", "")
        ).strip()

        if not player:
            continue

        # =============================================
        # DUPLICATE PLAYER SAME MATCH
        # =============================================

        if player in seen_players:
            continue

        seen_players.add(player)

        # =============================================
        # ABSURD CAREER TOTAL
        # =============================================

        if player_red_totals[player] > 8:
            continue

        # =============================================
        # MINUTE FILTER
        # =============================================

        minute_raw = str(
            red.get("minute", "")
        ).strip()

        minute_digits = ""

        for c in minute_raw:

            if c.isdigit():
                minute_digits += c

        try:
            minute = int(minute_digits)
        except:
            minute = 90

        # Most fake reds in your data are
        # actually yellow cards early in matches

        if minute < 35:
            continue

        cleaned.append(red)

    # =============================================
    # TOO MANY REDS IN ONE MATCH
    # =============================================

    if len(cleaned) > 2:
        cleaned = cleaned[:2]

    # =============================================
    # SAVE
    # =============================================

    if cleaned != reds:

        game["red_cards"] = cleaned

        with open(path, "w", encoding="utf-8") as f:

            json.dump(
                game,
                f,
                indent=2,
                ensure_ascii=False
            )

        fixed += 1

print("FILES FIXED:", fixed)
print("DONE")
