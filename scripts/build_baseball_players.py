import os
import json
import re
from collections import defaultdict

BASE = "docs/data/baseball"

BOX_DIR = f"{BASE}/boxscores"
PLAYERS_DIR = f"{BASE}/players"

INDEX_FILE = f"{BASE}/players.json"

os.makedirs(PLAYERS_DIR, exist_ok=True)

players = defaultdict(lambda: {
    "name": "",
    "slug": "",
    "career": {
        "games": 0,
        "AB": 0,
        "H": 0,
        "HR": 0,
        "AVG": ".000"
    },
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
# GET GAME ENTRY
# -------------------------

def get_game(player,date,season,team,opponent):

    for g in player["games"]:

        if (
            g["date"] == date and
            g["season"] == season and
            g["team"] == team and
            g["opponent"] == opponent
        ):
            return g

    game = {
        "date": date,
        "season": season,
        "team": team,
        "opponent": opponent,
        "AB": 0,
        "H": 0,
        "HR": 0
    }

    player["games"].append(game)

    return game

# -------------------------
# SCAN SEASONS
# -------------------------

season_dirs = sorted([
    d for d in os.listdir(BOX_DIR)
    if os.path.isdir(f"{BOX_DIR}/{d}")
])

for season in season_dirs:

    season_path = f"{BOX_DIR}/{season}"

    print(f"\nProcessing season {season}")

    box_files = sorted([
        f for f in os.listdir(season_path)
        if f.endswith(".json")
    ])

    print(f"Found {len(box_files)} boxscores")

    for bf in box_files:

        box_path = f"{season_path}/{bf}"

        try:

            with open(box_path,"r",encoding="utf-8") as f:
                box = json.load(f)

        except Exception as e:

            print(f"Failed {bf}: {e}")
            continue

        date = box.get("date","")

        home_code = (
            box.get("home_team",{})
            .get("code","")
        )

        away_code = (
            box.get("away_team",{})
            .get("code","")
        )

        plays = (
            box.get("liveData",{})
            .get("plays",{})
            .get("allPlays",[])
        )

        if not plays:
            continue

        for play in plays:

            batter = (
                play.get("matchup",{})
                .get("batter",{})
                .get("fullName","")
            ).strip()

            if not batter:
                continue

            slug = slugify(batter)

            player = players[slug]

            player["name"] = batter
            player["slug"] = slug

            is_top = (
                play.get("about",{})
                .get("isTopInning",False)
            )

            team = away_code if is_top else home_code
            opponent = home_code if is_top else away_code

            event_type = (
                play.get("result",{})
                .get("eventType","")
            )

            game = get_game(
                player,
                date,
                season,
                team,
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
# SAVE PLAYERS
# -------------------------

print("\nSaving players...")

index = []

for slug,data in players.items():

    games = data["games"]

    games.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    career_games = len(games)

    career_ab = sum(g["AB"] for g in games)
    career_hits = sum(g["H"] for g in games)
    career_hr = sum(g["HR"] for g in games)

    avg = (
        f"{career_hits / career_ab:.3f}"
        if career_ab else
        ".000"
    )

    if avg.startswith("0"):
        avg = avg[1:]

    data["career"] = {
        "games": career_games,
        "AB": career_ab,
        "H": career_hits,
        "HR": career_hr,
        "AVG": avg
    }

    out_path = f"{PLAYERS_DIR}/{slug}.json"

    with open(out_path,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2)

    index.append({
        "name": data["name"],
        "slug": slug
    })

# -------------------------
# SAVE INDEX
# -------------------------

index = sorted(
    index,
    key=lambda x: x["name"]
)

with open(INDEX_FILE,"w",encoding="utf-8") as f:
    json.dump(index,f,indent=2)

print(f"\nBuilt {len(players)} player files")
print("Saved players.json")
