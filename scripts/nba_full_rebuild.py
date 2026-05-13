import os
import json

SEASON_DIR = "docs/data/nba/2025"
GAMES_FILE = os.path.join(SEASON_DIR, "games.json")

print("RECOVERING NBA GAMES")

games = []

for filename in os.listdir(SEASON_DIR):

    if not filename.endswith(".json"):
        continue

    if filename in ["games.json", "index.json"]:
        continue

    path = os.path.join(SEASON_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:

        print(f"BAD FILE {filename}")
        continue

    # =========================================
    # SINGLE GAME OBJECT
    # =========================================

    if isinstance(data, dict):

        # MUST MATCH YOUR REAL GAME SCHEMA

        if (
            "home_team" in data
            and "away_team" in data
            and "game_id" in data
        ):

            games.append(data)

    # =========================================
    # ARRAY FILES
    # =========================================

    elif isinstance(data, list):

        for g in data:

            if not isinstance(g, dict):
                continue

            if (
                "home_team" in g
                and "away_team" in g
                and "game_id" in g
            ):

                games.append(g)

# =========================================
# REMOVE DUPLICATES
# =========================================

seen = set()
cleaned = []

for g in games:

    gid = str(g.get("game_id", ""))

    if gid:

        if gid in seen:
            continue

        seen.add(gid)

    cleaned.append(g)

# =========================================
# SORT
# =========================================

try:

    cleaned.sort(
        key=lambda x: x.get("date", "")
    )

except:
    pass

# =========================================
# SAVE
# =========================================

with open(
    GAMES_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        cleaned,
        f,
        indent=2
    )

print(f"RECOVERED {len(cleaned)} GAMES")
print("DONE")
