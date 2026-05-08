import os
import json
import glob
from collections import defaultdict

BASE = "docs/data/baseball"

BOX_DIR = f"{BASE}/boxscores"
PLAYERS_DIR = f"{BASE}/players"

os.makedirs(PLAYERS_DIR, exist_ok=True)

# ======================================================
# TEAM MAP
# ======================================================

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
    "KC":"Kansas City Royals",
    "LAA":"Los Angeles Angels",
    "LAD":"Los Angeles Dodgers",
    "MIA":"Miami Marlins",
    "MIL":"Milwaukee Brewers",
    "MIN":"Minnesota Twins",
    "NYM":"New York Mets",
    "NYY":"New York Yankees",
    "ATH":"Athletics",
    "PHI":"Philadelphia Phillies",
    "PIT":"Pittsburgh Pirates",
    "SD":"San Diego Padres",
    "SEA":"Seattle Mariners",
    "SF":"San Francisco Giants",
    "STL":"St Louis Cardinals",
    "TB":"Tampa Bay Rays",
    "TEX":"Texas Rangers",
    "TOR":"Toronto Blue Jays",
    "WSH":"Washington Nationals"
}

# ======================================================
# HELPERS
# ======================================================

def slugify(name):

    return (
        str(name)
        .lower()
        .replace(".", "")
        .replace("'", "")
        .replace(",", "")
        .replace(" jr", "-jr")
        .replace(" sr", "-sr")
        .replace(" ", "-")
    )

def add_game(players, player, game):

    if not player:
        return

    player = str(player).strip()

    if player.lower() in ["team", "totals"]:
        return

    players[player].append(game)

# ======================================================
# STORAGE
# ======================================================

players = defaultdict(list)

# ======================================================
# ALL BOXSCORES
# ======================================================

files = glob.glob(f"{BOX_DIR}/**/*.json", recursive=True)

print(f"FOUND {len(files)} BOXSCORES")

# ======================================================
# PROCESS
# ======================================================

for file in files:

    try:

        with open(file, "r", encoding="utf-8") as f:
            game = json.load(f)

    except Exception:
        continue

    season = str(game.get("season", ""))

    date = game.get("date", "")

    home_team = game.get("home_team", "")
    away_team = game.get("away_team", "")

    # ==================================================
    # RAW 2026 MLB API STYLE
    # ==================================================

    if "liveData" in game:

        try:

            box = (
                game.get("liveData", {})
                .get("boxscore", {})
                .get("teams", {})
            )

            home = box.get("home", {})
            away = box.get("away", {})

            home_players = home.get("players", {})
            away_players = away.get("players", {})

            # ------------------------------------------
            # HOME
            # ------------------------------------------

            for pid, pdata in home_players.items():

                person = pdata.get("person", {})
                stats = (
                    pdata.get("stats", {})
                    .get("batting", {})
                )

                player = person.get("fullName")

                add_game(players, player, {

                    "date": date,
                    "season": season,

                    "team": home_team,
                    "opponent": away_team,

                    "AB": stats.get("atBats", 0),
                    "R": stats.get("runs", 0),
                    "H": stats.get("hits", 0),
                    "RBI": stats.get("rbi", 0),
                    "HR": stats.get("homeRuns", 0),
                    "BB": stats.get("baseOnBalls", 0),
                    "SO": stats.get("strikeOuts", 0)

                })

            # ------------------------------------------
            # AWAY
            # ------------------------------------------

            for pid, pdata in away_players.items():

                person = pdata.get("person", {})
                stats = (
                    pdata.get("stats", {})
                    .get("batting", {})
                )

                player = person.get("fullName")

                add_game(players, player, {

                    "date": date,
                    "season": season,

                    "team": away_team,
                    "opponent": home_team,

                    "AB": stats.get("atBats", 0),
                    "R": stats.get("runs", 0),
                    "H": stats.get("hits", 0),
                    "RBI": stats.get("rbi", 0),
                    "HR": stats.get("homeRuns", 0),
                    "BB": stats.get("baseOnBalls", 0),
                    "SO": stats.get("strikeOuts", 0)

                })

        except Exception as e:

            print(f"FAILED RAW {file}")
            print(e)

    # ==================================================
    # OLD STRUCTURE
    # ==================================================

    else:

        try:

            home_batting = game.get("home_batting", [])
            away_batting = game.get("away_batting", [])

            for p in home_batting:

                add_game(players, p.get("player"), {

                    "date": date,
                    "season": season,

                    "team": home_team,
                    "opponent": away_team,

                    "AB": p.get("AB", 0),
                    "R": p.get("R", 0),
                    "H": p.get("H", 0),
                    "RBI": p.get("RBI", 0),
                    "HR": p.get("HR", 0),
                    "BB": p.get("BB", 0),
                    "SO": p.get("SO", 0)

                })

            for p in away_batting:

                add_game(players, p.get("player"), {

                    "date": date,
                    "season": season,

                    "team": away_team,
                    "opponent": home_team,

                    "AB": p.get("AB", 0),
                    "R": p.get("R", 0),
                    "H": p.get("H", 0),
                    "RBI": p.get("RBI", 0),
                    "HR": p.get("HR", 0),
                    "BB": p.get("BB", 0),
                    "SO": p.get("SO", 0)

                })

        except Exception:
            continue

# ======================================================
# BUILD PLAYER FILES
# ======================================================

count = 0

for player_name, games in players.items():

    slug = slugify(player_name)

    games.sort(
        key=lambda x: x.get("date", ""),
        reverse=True
    )

    totals = {
        "games": len(games),
        "AB": 0,
        "R": 0,
        "H": 0,
        "RBI": 0,
        "HR": 0,
        "BB": 0,
        "SO": 0
    }

    for g in games:

        totals["AB"] += int(g.get("AB", 0) or 0)
        totals["R"] += int(g.get("R", 0) or 0)
        totals["H"] += int(g.get("H", 0) or 0)
        totals["RBI"] += int(g.get("RBI", 0) or 0)
        totals["HR"] += int(g.get("HR", 0) or 0)
        totals["BB"] += int(g.get("BB", 0) or 0)
        totals["SO"] += int(g.get("SO", 0) or 0)

    avg = (
        totals["H"] / totals["AB"]
        if totals["AB"] else 0
    )

    totals["AVG"] = f"{avg:.3f}"

    out = {

        "name": player_name,
        "slug": slug,

        "career": totals,

        "games": games

    }

    with open(
        f"{PLAYERS_DIR}/{slug}.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            out,
            f,
            indent=2,
            ensure_ascii=False
        )

    count += 1

print(f"BUILT {count} PLAYER FILES")
