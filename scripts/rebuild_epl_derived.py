import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"

duplicates = defaultdict(list)

def clean(v):
    return str(v or "").strip()

print("SCANNING FOR DUPLICATE EPL MATCHES")

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in sorted(files):

        if not file.endswith(".json"):
            continue

        path = os.path.join(root, file)

        try:

            with open(path, "r", encoding="utf-8") as f:
                game = json.load(f)

        except Exception:
            continue

        if not isinstance(game, dict):
            continue

        home = clean(game.get("home_team"))
        away = clean(game.get("away_team"))

        if not home or not away:
            continue

        date = clean(
            game.get("date")
            or game.get("match_date")
        )

        season = clean(
            game.get("season")
            or game.get("year")
            or path.split("/")[-2]
        )

        home_score = clean(game.get("home_score"))
        away_score = clean(game.get("away_score"))

        venue = clean(game.get("venue"))

        # =================================================
        # DUPLICATE SIGNATURE
        # =================================================

        sig = (
            f"{season}|"
            f"{date}|"
            f"{home}|"
            f"{away}|"
            f"{home_score}|"
            f"{away_score}|"
            f"{venue}"
        )

        duplicates[sig].append(path)

# =====================================================
# RESULTS
# =====================================================

dupe_count = 0

for sig, paths in duplicates.items():

    if len(paths) <= 1:
        continue

    dupe_count += 1

    print("\n=================================================")
    print("DUPLICATE MATCH")
    print(sig)
    print("-------------------------------------------------")

    for p in paths:
        print(p)

print("\n=================================================")
print("TOTAL DUPLICATE MATCH GROUPS:", dupe_count)
print("DONE")
