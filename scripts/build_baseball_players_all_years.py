import os
import json
import re
from collections import defaultdict

BASE = "docs/data/baseball"
BOX_DIR = os.path.join(BASE, "boxscores")
PLAYERS_DIR = os.path.join(BASE, "players")

RETRO_FILE = os.path.join(BASE, "retro_players.json")
PLAYERS_FILE = os.path.join(BASE, "players.json")

os.makedirs(PLAYERS_DIR, exist_ok=True)

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def slugify(name):
    name = str(name or "").lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    return name

TEAM_NAMES = {
    "ARI":"Arizona Diamondbacks",
    "ATL":"Atlanta Braves",
    "BAL":"Baltimore Orioles",
    "BOS":"Boston Red Sox",
    "CHC":"Chicago Cubs",
    "CHN":"Chicago Cubs",
    "CHW":"Chicago White Sox",
    "CIN":"Cincinnati Reds",
    "CLE":"Cleveland Guardians",
    "COL":"Colorado Rockies",
    "DET":"Detroit Tigers",
    "HOU":"Houston Astros",
    "KC":"Kansas City Royals",
    "KAN":"Kansas City Royals",
    "LAA":"Los Angeles Angels",
    "LAD":"Los Angeles Dodgers",
    "LAN":"Los Angeles Dodgers",
    "LOS":"Los Angeles Dodgers",
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
    "WSH":"Washington Nationals",
    "WSN":"Washington Nationals"
}

retro_lookup = {}
retro_data = load_json(RETRO_FILE)

if isinstance(retro_data, dict):
    retro_lookup = retro_data

elif isinstance(retro_data, list):

    for r in retro_data:

        if not isinstance(r, dict):
            continue

        pid = (
            r.get("id")
            or r.get("player_id")
            or r.get("retro_id")
        )

        name = (
            r.get("name")
            or r.get("full_name")
            or r.get("player")
        )

        if pid and name:
            retro_lookup[str(pid)] = name

modern_lookup = {}
modern_data = load_json(PLAYERS_FILE)

if isinstance(modern_data, list):

    for r in modern_data:

        if not isinstance(r, dict):
            continue

        pid = (
            r.get("id")
            or r.get("player_id")
            or r.get("retro_id")
        )

        name = (
            r.get("name")
            or r.get("full_name")
            or r.get("player")
        )

        if pid and name:
            modern_lookup[str(pid)] = name

def resolve_name(pid):

    pid = str(pid)

    if pid in retro_lookup:
        return retro_lookup[pid]

    if pid in modern_lookup:
        return modern_lookup[pid]

    return pid

def team_name(code):
    return TEAM_NAMES.get(str(code), str(code))

players = defaultdict(lambda:{
    "name":"",
    "games":[]
})

def add_game(name, row):

    slug = slugify(name)

    players[slug]["name"] = name
    players[slug]["games"].append(row)

for season in sorted(os.listdir(BOX_DIR)):

    season_dir = os.path.join(BOX_DIR, season)

    if not os.path.isdir(season_dir):
        continue

    print("Season", season)

    for file in sorted(os.listdir(season_dir)):

        if not file.endswith(".json"):
            continue

        path = os.path.join(season_dir, file)

        game = load_json(path)

        if not isinstance(game, dict):
            continue

        date = game.get("date", "")
        season_value = game.get("season", season)

        # =========================
        # RETROSHEET
        # =========================

        if "events" in game:

            home = game.get("home_code")
            away = game.get("away_code")

            totals = {}

            for ev in game.get("events", []):

                if not isinstance(ev, list):
                    continue

                if len(ev) < 7:
                    continue

                if ev[0] != "play":
                    continue

                side = str(ev[2])
                pid = ev[3]
                result = str(ev[6]).upper()

                if not pid:
                    continue

                player_name = resolve_name(pid)

                if side == "0":
                    team = away
                    opp = home
                else:
                    team = home
                    opp = away

                key = (
                    player_name,
                    team,
                    opp
                )

                if key not in totals:

                    totals[key] = {
                        "date": date,
                        "season": season_value,
                        "team": team_name(team),
                        "opponent": team_name(opp),
                        "AB":0,
                        "R":0,
                        "H":0,
                        "RBI":0,
                        "HR":0,
                        "BB":0,
                        "SO":0
                    }

                g = totals[key]

                if result.startswith("W") or result.startswith("IW"):
                    g["BB"] += 1

                elif result.startswith("K"):
                    g["AB"] += 1
                    g["SO"] += 1

                elif result.startswith("S"):
                    g["AB"] += 1
                    g["H"] += 1

                elif result.startswith("D"):
                    g["AB"] += 1
                    g["H"] += 1

                elif result.startswith("T"):
                    g["AB"] += 1
                    g["H"] += 1

                elif result.startswith("HR"):
                    g["AB"] += 1
                    g["H"] += 1
                    g["HR"] += 1
                    g["R"] += 1

                elif re.match(r"^[0-9]", result):
                    g["AB"] += 1

            for (player_name, _, _), row in totals.items():
                add_game(player_name, row)

        # =========================
        # MLB API
        # =========================

        elif "liveData" in game:

            teams = (
                game.get("liveData", {})
                    .get("boxscore", {})
                    .get("teams", {})
            )

            home_team = game.get("home_team", {})
            away_team = game.get("away_team", {})

            for side in ["home", "away"]:

                players_block = (
                    teams.get(side, {})
                         .get("players", {})
                )

                for _, p in players_block.items():

                    person = p.get("person", {})

                    name = (
                        person.get("fullName")
                        or person.get("boxscoreName")
                    )

                    if not name:
                        continue

                    batting = (
                        p.get("stats", {})
                         .get("batting", {})
                    )

                    if not batting:
                        continue

                    row = {
                        "date": date,
                        "season": season_value,
                        "team": team_name(
                            home_team["code"]
                            if side == "home"
                            else away_team["code"]
                        ),
                        "opponent": team_name(
                            away_team["code"]
                            if side == "home"
                            else home_team["code"]
                        ),
                        "AB": int(batting.get("atBats",0) or 0),
                        "R": int(batting.get("runs",0) or 0),
                        "H": int(batting.get("hits",0) or 0),
                        "RBI": int(batting.get("rbi",0) or 0),
                        "HR": int(batting.get("homeRuns",0) or 0),
                        "BB": int(batting.get("baseOnBalls",0) or 0),
                        "SO": int(batting.get("strikeOuts",0) or 0)
                    }

                    add_game(name, row)

index = []

for slug, pdata in players.items():

    pdata["games"].sort(
        key=lambda x: str(x.get("date","")),
        reverse=True
    )

    save_json(
        os.path.join(PLAYERS_DIR, f"{slug}.json"),
        pdata
    )

    index.append({
        "name": pdata["name"],
        "slug": slug,
        "games": len(pdata["games"])
    })

save_json(
    os.path.join(PLAYERS_DIR, "index.json"),
    sorted(index, key=lambda x:x["name"])
)

print("DONE")
print("Player files:", len(players))
