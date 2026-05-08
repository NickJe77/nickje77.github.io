import os
import json
import glob
from collections import defaultdict

BASE = "docs/data/baseball"

SEASONS_DIR = f"{BASE}/seasons"
BOXSCORE_DIR = f"{BASE}/boxscores"
PLAYERS_DIR = f"{BASE}/players"

os.makedirs(PLAYERS_DIR, exist_ok=True)

# =========================================================
# TEAM MAP
# =========================================================

TEAM_MAP = {

    "Arizona Diamondbacks":"ARI",
    "Atlanta Braves":"ATL",
    "Baltimore Orioles":"BAL",
    "Boston Red Sox":"BOS",
    "Chicago Cubs":"CHC",
    "Chicago White Sox":"CHW",
    "Cincinnati Reds":"CIN",
    "Cleveland Guardians":"CLE",
    "Colorado Rockies":"COL",
    "Detroit Tigers":"DET",
    "Houston Astros":"HOU",
    "Kansas City Royals":"KC",
    "Los Angeles Angels":"LAA",
    "Los Angeles Dodgers":"LAD",
    "Miami Marlins":"MIA",
    "Milwaukee Brewers":"MIL",
    "Minnesota Twins":"MIN",
    "New York Mets":"NYM",
    "New York Yankees":"NYY",
    "Athletics":"ATH",
    "Oakland Athletics":"ATH",
    "Philadelphia Phillies":"PHI",
    "Pittsburgh Pirates":"PIT",
    "San Diego Padres":"SD",
    "Seattle Mariners":"SEA",
    "San Francisco Giants":"SF",
    "St Louis Cardinals":"STL",
    "St. Louis Cardinals":"STL",
    "Tampa Bay Rays":"TB",
    "Texas Rangers":"TEX",
    "Toronto Blue Jays":"TOR",
    "Washington Nationals":"WSH",

    "ARI":"ARI",
    "ATL":"ATL",
    "BAL":"BAL",
    "BOS":"BOS",
    "CHC":"CHC",
    "CHW":"CHW",
    "CIN":"CIN",
    "CLE":"CLE",
    "COL":"COL",
    "DET":"DET",
    "HOU":"HOU",
    "KC":"KC",
    "KAN":"KC",
    "LAA":"LAA",
    "LAD":"LAD",
    "LOS":"LAD",
    "MIA":"MIA",
    "MIL":"MIL",
    "MIN":"MIN",
    "NYM":"NYM",
    "NYY":"NYY",
    "ATH":"ATH",
    "OAK":"ATH",
    "PHI":"PHI",
    "PIT":"PIT",
    "SD":"SD",
    "SDP":"SD",
    "SEA":"SEA",
    "SF":"SF",
    "SFG":"SF",
    "STL":"STL",
    "TB":"TB",
    "TBR":"TB",
    "TEX":"TEX",
    "TOR":"TOR",
    "WSH":"WSH",
    "WSN":"WSH"
}

# =========================================================
# HELPERS
# =========================================================

def slugify(name):

    return (
        str(name)
        .lower()
        .replace(".","")
        .replace("'","")
        .replace(",","")
        .replace(" jr","-jr")
        .replace(" sr","-sr")
        .replace(" ","-")
    )

def clean_name(name):

    if not name:
        return None

    name = str(name).strip()

    if name.lower() in ["team","totals"]:
        return None

    return name

def team_code(team):

    if not team:
        return ""

    return TEAM_MAP.get(team, team)

# =========================================================
# PLAYER STORAGE
# =========================================================

players = defaultdict(list)

# =========================================================
# LOOP ALL BOXSCORE FILES
# =========================================================

boxscore_files = sorted(
    glob.glob(f"{BOXSCORE_DIR}/**/*.json", recursive=True)
)

print(f"FOUND {len(boxscore_files)} BOXSCORES")

# =========================================================
# PROCESS
# =========================================================

for file in boxscore_files:

    try:

        with open(file, "r", encoding="utf-8") as f:
            game = json.load(f)

    except Exception as e:

        print(f"FAILED {file}")
        print(e)
        continue

    season = str(game.get("season", ""))

    date = game.get("date", "")

    home_team = team_code(
        game.get("home_team")
        or game.get("home")
        or ""
    )

    away_team = team_code(
        game.get("away_team")
        or game.get("away")
        or ""
    )

    # =====================================================
    # FIND BATTING TABLES
    # =====================================================

    possible_home = [

        game.get("home_batting"),
        game.get("homeBatting"),
        game.get("home_players"),
        game.get("homePlayers"),
        game.get("batting_home"),
        game.get("batters_home")

    ]

    possible_away = [

        game.get("away_batting"),
        game.get("awayBatting"),
        game.get("away_players"),
        game.get("awayPlayers"),
        game.get("batting_away"),
        game.get("batters_away")

    ]

    home_batting = []
    away_batting = []

    for p in possible_home:
        if isinstance(p, list) and len(p):
            home_batting = p
            break

    for p in possible_away:
        if isinstance(p, list) and len(p):
            away_batting = p
            break

    # =====================================================
    # HOME PLAYERS
    # =====================================================

    for p in home_batting:

        player = clean_name(
            p.get("player")
            or p.get("name")
        )

        if not player:
            continue

        players[player].append({

            "date": date,
            "season": season,

            "team": home_team,
            "opponent": away_team,

            "AB": int(p.get("AB",0) or 0),
            "R": int(p.get("R",0) or 0),
            "H": int(p.get("H",0) or 0),
            "RBI": int(p.get("RBI",0) or 0),
            "HR": int(p.get("HR",0) or 0),
            "BB": int(p.get("BB",0) or 0),
            "SO": int(p.get("SO",0) or 0)

        })

    # =====================================================
    # AWAY PLAYERS
    # =====================================================

    for p in away_batting:

        player = clean_name(
            p.get("player")
            or p.get("name")
        )

        if not player:
            continue

        players[player].append({

            "date": date,
            "season": season,

            "team": away_team,
            "opponent": home_team,

            "AB": int(p.get("AB",0) or 0),
            "R": int(p.get("R",0) or 0),
            "H": int(p.get("H",0) or 0),
            "RBI": int(p.get("RBI",0) or 0),
            "HR": int(p.get("HR",0) or 0),
            "BB": int(p.get("BB",0) or 0),
            "SO": int(p.get("SO",0) or 0)

        })

# =========================================================
# BUILD PLAYER FILES
# =========================================================

count = 0

for player_name, games in players.items():

    slug = slugify(player_name)

    games.sort(
        key=lambda x: x.get("date",""),
        reverse=True
    )

    totals = {

        "games": len(games),

        "AB": sum(int(g.get("AB",0)) for g in games),
        "R": sum(int(g.get("R",0)) for g in games),
        "H": sum(int(g.get("H",0)) for g in games),
        "RBI": sum(int(g.get("RBI",0)) for g in games),
        "HR": sum(int(g.get("HR",0)) for g in games),
        "BB": sum(int(g.get("BB",0)) for g in games),
        "SO": sum(int(g.get("SO",0)) for g in games)

    }

    avg = (
        totals["H"] / totals["AB"]
        if totals["AB"] else 0
    )

    totals["AVG"] = f"{avg:.3f}"

    player_json = {

        "name": player_name,
        "slug": slug,

        "career": totals,

        "games": games

    }

    out_file = f"{PLAYERS_DIR}/{slug}.json"

    with open(out_file, "w", encoding="utf-8") as f:

        json.dump(
            player_json,
            f,
            indent=2,
            ensure_ascii=False
        )

    count += 1

print(f"\nBUILT {count} PLAYER FILES")
