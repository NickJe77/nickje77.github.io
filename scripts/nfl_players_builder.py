import os
import json
import re
from collections import defaultdict
from unidecode import unidecode

BASE_DIR = "docs/data/nfl"
BOXSCORE_DIR = f"{BASE_DIR}/boxscores"
PLAYERS_DIR = f"{BASE_DIR}/players"

os.makedirs(PLAYERS_DIR, exist_ok=True)

MASTER = {}
PLAYER_GAMES = defaultdict(list)

STAT_SECTIONS = [
    "passing",
    "rushing",
    "receiving",
    "defense",
    "kicking",
    "punting",
    "returns"
]

# ---------------------------------------------------
# SLUG
# ---------------------------------------------------

def slugify(name):
    name = unidecode(name)
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    return name

# ---------------------------------------------------
# SAFE LOAD
# ---------------------------------------------------

def safe_load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

# ---------------------------------------------------
# PROCESS BOXSCORES
# ---------------------------------------------------

for season in sorted(os.listdir(BOXSCORE_DIR)):

    season_dir = os.path.join(BOXSCORE_DIR, season)

    if not os.path.isdir(season_dir):
        continue

    print(f"Processing {season}")

    for file in os.listdir(season_dir):

        if not file.endswith(".json"):
            continue

        path = os.path.join(season_dir, file)

        game = safe_load(path)

        if not game:
            continue

        game_id = game.get("game_id", file.replace(".json", ""))

        for section in STAT_SECTIONS:

            rows = game.get(section, [])

            if not isinstance(rows, list):
                continue

            for row in rows:

                player = row.get("player")

                if not player:
                    continue

                slug = slugify(player)

                stats = row.get("stats", {})

                team = stats.get("team", "")

                if slug not in MASTER:

                    MASTER[slug] = {
                        "player_id": slug,
                        "name": player,
                        "teams": set(),
                        "seasons": set(),
                        "games": 0
                    }

                MASTER[slug]["teams"].add(team)
                MASTER[slug]["seasons"].add(int(season))
                MASTER[slug]["games"] += 1

                PLAYER_GAMES[slug].append({
                    "game_id": game_id,
                    "season": int(season),
                    "section": section,
                    "stats": stats
                })

# ---------------------------------------------------
# BUILD MASTER
# ---------------------------------------------------

master_output = []

for slug, info in MASTER.items():

    obj = {
        "player_id": slug,
        "name": info["name"],
        "teams": sorted(list(info["teams"])),
        "seasons": sorted(list(info["seasons"])),
        "games": info["games"]
    }

    master_output.append(obj)

master_output.sort(key=lambda x: x["name"])

# ---------------------------------------------------
# SAVE players.json
# ---------------------------------------------------

with open(f"{BASE_DIR}/players.json", "w", encoding="utf-8") as f:
    json.dump(master_output, f, indent=2)

# ---------------------------------------------------
# SAVE index.json
# ---------------------------------------------------

with open(f"{PLAYERS_DIR}/index.json", "w", encoding="utf-8") as f:
    json.dump(master_output, f, indent=2)

# ---------------------------------------------------
# SAVE INDIVIDUAL PLAYER FILES
# ---------------------------------------------------

for slug, games in PLAYER_GAMES.items():

    meta = MASTER[slug]

    player_obj = {
        "player_id": slug,
        "name": meta["name"],
        "teams": sorted(list(meta["teams"])),
        "seasons": sorted(list(meta["seasons"])),
        "games": games
    }

    with open(f"{PLAYERS_DIR}/{slug}.json", "w", encoding="utf-8") as f:
        json.dump(player_obj, f, indent=2)

print("DONE")
