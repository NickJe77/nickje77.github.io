import os
import json
import re
from collections import defaultdict
from unidecode import unidecode

BASE_DIR = "docs/data/nfl"
BOXSCORE_DIR = f"{BASE_DIR}/boxscores"
PLAYERS_DIR = f"{BASE_DIR}/players"

os.makedirs(PLAYERS_DIR, exist_ok=True)

MASTER_PLAYERS = {}
PLAYER_GAMES = defaultdict(list)

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
# FIND ALL BOXSCORES
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

        home_team = game.get("home_team", "")
        away_team = game.get("away_team", "")

        date = game.get("date", "")

        # ---------------------------------------------------
        # PLAYER STATS
        # ---------------------------------------------------

        player_stats = game.get("player_stats", {})

        for stat_group, players in player_stats.items():

            if not isinstance(players, list):
                continue

            for row in players:

                player_name = row.get("player")

                if not player_name:
                    continue

                slug = slugify(player_name)

                team = row.get("team", "")

                MASTER_PLAYERS.setdefault(slug, {
                    "player_id": slug,
                    "name": player_name,
                    "teams": set(),
                    "seasons": set(),
                    "games": 0
                })

                MASTER_PLAYERS[slug]["teams"].add(team)
                MASTER_PLAYERS[slug]["seasons"].add(int(season))
                MASTER_PLAYERS[slug]["games"] += 1

                PLAYER_GAMES[slug].append({
                    "game_id": game_id,
                    "season": int(season),
                    "date": date,
                    "team": team,
                    "opponent": away_team if team == home_team else home_team,
                    "stats": row
                })

# ---------------------------------------------------
# BUILD MASTER FILE
# ---------------------------------------------------

master_output = []

for slug, info in MASTER_PLAYERS.items():

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
# SAVE INDIVIDUAL FILES
# ---------------------------------------------------

for slug, games in PLAYER_GAMES.items():

    meta = MASTER_PLAYERS[slug]

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
