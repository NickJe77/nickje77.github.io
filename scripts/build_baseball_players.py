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

    replacements = {
        "á":"a","à":"a","ä":"a","â":"a",
        "é":"e","è":"e","ë":"e","ê":"e",
        "í":"i","ì":"i","ï":"i","î":"i",
        "ó":"o","ò":"o","ö":"o","ô":"o",
        "ú":"u","ù":"u","ü":"u","û":"u",
        "ñ":"n"
    }

    for k,v in replacements.items():
        name = name.replace(k,v)

    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)

    return name

# -------------------------
# GET GAME ENTRY
# -------------------------

def get_game(player, date, season, team, opponent):

    for g in player["games"]:

        if (
            g["date"] == date and
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
# LOAD SEASONS
# -------------------------

season_files = sorted([
    f for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
])

for sf in season_files:

    season = sf.replace(".json","")

    print(f"Processing season {season}")

    season_path = f"{SEASONS_DIR}/{sf}"

    try:
        with open(season_path,"r",encoding="utf-8") as f:
            season_games = json.load(f)
    except Exception as e:
        print(f"Failed season {season}: {e}")
        continue

    if not isinstance(season_games,list):
        continue

    for g in season_games:

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
            with open(box_path,"r",encoding="utf-8") as f:
                box = json.load(f)
        except:
            continue

        date = (
            box.get("date") or
            g.get("date") or
            ""
        )

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

            matchup = play.get("matchup",{})

            batter = matchup.get("batter",{})

            name = (
                batter.get("fullName","")
            ).strip()

            if not name:
                continue

            slug = slugify(name)

            player = players[slug]

            player["name"] = name
            player["slug"] = slug

            about = play.get("about",{})

            is_top = about.get("isTopInning",False)

            team = away_code if is_top else home_code
            opponent = home_code if is_top else away_code

            result = play.get("result",{})

            event_type = result.get("eventType","")

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
            # HOME RUNS
            # -------------------------

            if event_type == "home_run":
                game["HR"] += 1

# -------------------------
# BUILD CAREER TOTALS
# -------------------------

print("Building career totals...")

index = []

for slug,data in players.items():

    games = data["games"]

    games.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    career_games = len(games)

    career_ab = sum(
        g.get("AB",0)
        for g in games
    )

    career_hits = sum(
        g.get("H",0)
        for g in games
    )

    career_hr = sum(
        g.get("HR",0)
        for g in games
    )

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

print(f"Built {len(players)} player files")
print("Saved players.json")
