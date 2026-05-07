import os
import json
import re
from collections import defaultdict

BASE = "docs/data/baseball"

BOX_DIR = f"{BASE}/boxscores"
PLAYERS_DIR = f"{BASE}/players"

INDEX_FILE = f"{BASE}/players.json"

os.makedirs(PLAYERS_DIR, exist_ok=True)

TEAM_MAP = {
    "ARI":"Arizona Diamondbacks",
    "ATL":"Atlanta Braves",
    "BAL":"Baltimore Orioles",
    "BOS":"Boston Red Sox",
    "CHC":"Chicago Cubs",
    "CHW":"Chicago White Sox",
    "CIN":"Cincinnati Reds",
    "CLE":"Cleveland Guardians",
    "COL":"Colorado Rockies",
    "DET":"Detroit Tigers",
    "HOU":"Houston Astros",
    "KAN":"Kansas City Royals",
    "KC":"Kansas City Royals",
    "LAA":"Los Angeles Angels",
    "LAD":"Los Angeles Dodgers",
    "MIA":"Miami Marlins",
    "MIL":"Milwaukee Brewers",
    "MIN":"Minnesota Twins",
    "NYM":"New York Mets",
    "NYY":"New York Yankees",
    "ATH":"Athletics",
    "OAK":"Athletics",
    "PHI":"Philadelphia Phillies",
    "PIT":"Pittsburgh Pirates",
    "SD":"San Diego Padres",
    "SDP":"San Diego Padres",
    "SEA":"Seattle Mariners",
    "SF":"San Francisco Giants",
    "SFG":"San Francisco Giants",
    "STL":"St Louis Cardinals",
    "TB":"Tampa Bay Rays",
    "TBR":"Tampa Bay Rays",
    "TEX":"Texas Rangers",
    "TOR":"Toronto Blue Jays",
    "WAS":"Washington Nationals",
    "WSN":"Washington Nationals"
}

players = defaultdict(lambda: {
    "name":"",
    "slug":"",
    "career":{
        "games":0,
        "AB":0,
        "H":0,
        "HR":0,
        "AVG":".000"
    },
    "games":[]
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
# GET GAME
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
        "date":date,
        "season":season,
        "team":team,
        "opponent":opponent,
        "AB":0,
        "H":0,
        "HR":0
    }

    player["games"].append(game)

    return game

# -------------------------
# SCAN BOXES
# -------------------------

season_dirs = sorted([
    d for d in os.listdir(BOX_DIR)
    if os.path.isdir(f"{BOX_DIR}/{d}")
])

for season in season_dirs:

    print(f"\nProcessing {season}")

    season_path = f"{BOX_DIR}/{season}"

    files = sorted([
        f for f in os.listdir(season_path)
        if f.endswith(".json")
    ])

    print(f"Found {len(files)} files")

    for bf in files:

        box_path = f"{season_path}/{bf}"

        try:

            with open(box_path,"r",encoding="utf-8") as f:
                box = json.load(f)

        except:
            continue

        date = box.get("date","")

        # -------------------------
        # TEAMS
        # -------------------------

        home_code = (
            box.get("home_code") or
            box.get("home_team") or
            ""
        )

        away_code = (
            box.get("away_code") or
            box.get("away_team") or
            ""
        )

        if isinstance(home_code,dict):
            home_code = home_code.get("code","")

        if isinstance(away_code,dict):
            away_code = away_code.get("code","")

        home_team = TEAM_MAP.get(
            home_code,
            str(home_code)
        )

        away_team = TEAM_MAP.get(
            away_code,
            str(away_code)
        )

        # -------------------------
        # MODERN MLB
        # -------------------------

        plays = (
            box.get("liveData",{})
            .get("plays",{})
            .get("allPlays",[])
        )

        if plays:

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

                team = away_team if is_top else home_team
                opponent = home_team if is_top else away_team

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

                if event_type not in [
                    "walk",
                    "intent_walk",
                    "hit_by_pitch",
                    "sac_bunt",
                    "sac_fly"
                ]:
                    game["AB"] += 1

                if event_type in [
                    "single",
                    "double",
                    "triple",
                    "home_run"
                ]:
                    game["H"] += 1

                if event_type == "home_run":
                    game["HR"] += 1

        # -------------------------
        # OLD MLB STRUCTURE
        # -------------------------

        else:

            for side in ["home","away"]:

                hitters = (
                    box.get(f"{side}_batters") or
                    box.get(f"batters_{side}") or
                    box.get(f"batting_{side}") or
                    []
                )

                if not hitters:
                    continue

                for p in hitters:

                    name = (
                        p.get("name") or
                        p.get("player") or
                        p.get("fullName") or
                        ""
                    ).strip()

                    if not name:
                        continue

                    slug = slugify(name)

                    player = players[slug]

                    player["name"] = name
                    player["slug"] = slug

                    team = (
                        home_team
                        if side == "home"
                        else away_team
                    )

                    opponent = (
                        away_team
                        if side == "home"
                        else home_team
                    )

                    game = get_game(
                        player,
                        date,
                        season,
                        team,
                        opponent
                    )

                    game["AB"] += int(
                        p.get("AB") or
                        p.get("ab") or
                        0
                    )

                    game["H"] += int(
                        p.get("H") or
                        p.get("h") or
                        0
                    )

                    game["HR"] += int(
                        p.get("HR") or
                        p.get("hr") or
                        0
                    )

# -------------------------
# SAVE
# -------------------------

print("\nSaving players")

index = []

for slug,data in players.items():

    games = data["games"]

    games.sort(
        key=lambda x:x["date"],
        reverse=True
    )

    ab = sum(g["AB"] for g in games)
    hits = sum(g["H"] for g in games)
    hr = sum(g["HR"] for g in games)

    avg = (
        f"{hits/ab:.3f}"
        if ab else
        ".000"
    )

    if avg.startswith("0"):
        avg = avg[1:]

    data["career"] = {
        "games":len(games),
        "AB":ab,
        "H":hits,
        "HR":hr,
        "AVG":avg
    }

    out_path = f"{PLAYERS_DIR}/{slug}.json"

    with open(out_path,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2)

    index.append({
        "name":data["name"],
        "slug":slug
    })

index = sorted(
    index,
    key=lambda x:x["name"]
)

with open(INDEX_FILE,"w",encoding="utf-8") as f:
    json.dump(index,f,indent=2)

print(f"Built {len(players)} players")
