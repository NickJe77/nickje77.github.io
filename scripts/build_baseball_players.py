import os
import json
import re
from collections import defaultdict

BASE = "docs/data/baseball"

SEASONS_DIR = f"{BASE}/seasons"
BOX_DIR = f"{BASE}/boxscores"

PLAYERS_DIR = f"{BASE}/players"
INDEX_FILE = f"{BASE}/players.json"

os.makedirs(PLAYERS_DIR, exist_ok=True)

players = defaultdict(lambda: {
    "name": "",
    "slug": "",
    "games": []
})

# -------------------------
# SLUGIFY
# -------------------------

def slugify(name):

    name = name.lower().strip()

    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)

    return name

# -------------------------
# SAFE GET PLAYER GAME
# -------------------------

def get_game_entry(player, date, team, opponent):

    for g in player["games"]:

        if (
            g["date"] == date and
            g["team"] == team and
            g["opponent"] == opponent
        ):
            return g

    game = {
        "date": date,
        "team": team,
        "opponent": opponent,
        "AB": 0,
        "H": 0,
        "HR": 0,
        "RBI": 0
    }

    player["games"].append(game)

    return game

# -------------------------
# LOAD SEASONS
# -------------------------

season_files = sorted([
    f for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
])

for sf in season_files:

    season = sf.replace(".json", "")

    print(f"Processing {season}")

    season_path = f"{SEASONS_DIR}/{sf}"

    try:
        with open(season_path, "r", encoding="utf-8") as f:
            games = json.load(f)
    except:
        continue

    if not isinstance(games, list):
        continue

    for g in games:

        file_name = (
            g.get("game_file") or
            g.get("filename") or
            g.get("file") or
            ""
        )

        if not file_name:
            continue

        if not file_name.endswith(".json"):
            file_name += ".json"

        box_path = f"{BOX_DIR}/{season}/{file_name}"

        if not os.path.exists(box_path):
            continue

        try:
            with open(box_path, "r", encoding="utf-8") as f:
                box = json.load(f)
        except:
            continue

        date = box.get("date", "")

        home_code = (
            box.get("home_team", {})
            .get("code", "")
        )

        away_code = (
            box.get("away_team", {})
            .get("code", "")
        )

        plays = (
            box.get("liveData", {})
            .get("plays", {})
            .get("allPlays", [])
        )

        for play in plays:

            matchup = play.get("matchup", {})

            batter = matchup.get("batter", {})

            name = batter.get("fullName", "").strip()

            if not name:
                continue

            about = play.get("about", {})

            is_top = about.get("isTopInning", False)

            batting_team = away_code if is_top else home_code
            opponent = home_code if is_top else away_code

            result = play.get("result", {})

            event_type = result.get("eventType", "")
            rbi = result.get("rbi", 0)

            slug = slugify(name)

            player = players[slug]

            player["name"] = name
            player["slug"] = slug

            game = get_game_entry(
                player,
                date,
                batting_team,
                opponent
            )

            # -------------------------
            # AB
            # -------------------------

            if event_type not in [
                "walk",
                "intent_walk",
                "hit_by_pitch",
                "sac_bunt",
                "sac_fly"
            ]:
                game["AB"] += 1

            # -------------------------
            # HITS
            # -------------------------

            if event_type in [
                "single",
                "double",
                "triple",
                "home_run"
            ]:
                game["H"] += 1

            # -------------------------
            # HR
            # -------------------------

            if event_type == "home_run":
                game["HR"] += 1

            # -------------------------
            # RBI
            # -------------------------

            game["RBI"] += int(rbi)

# -------------------------
# SAVE FILES
# -------------------------

print("Saving player files...")

index = []

for slug, data in players.items():

    out_path = f"{PLAYERS_DIR}/{slug}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    index.append({
        "name": data["name"],
        "slug": slug
    })

index = sorted(index, key=lambda x: x["name"])

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2)

print(f"Built {len(players)} player files")
