import os
import csv
import json
import glob
from collections import defaultdict

BASE = "docs/data/baseball"

BOX_DIR = f"{BASE}/boxscores"
PLAYERS_DIR = f"{BASE}/players"

import shutil
if os.path.exists(PLAYERS_DIR):
    shutil.rmtree(PLAYERS_DIR)
os.makedirs(PLAYERS_DIR)

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
# RETROSHEET PLAYER ID LOOKUP
# ======================================================

RETRO_PLAYERS = {}

biofile_path = "docs/data/baseball/biofile0.csv"

if os.path.exists(biofile_path):
    with open(biofile_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get("id", "").strip()
            first = row.get("usename", "").strip()
            last = row.get("lastname", "").strip()
            name = f"{first} {last}" if first and last else ""
            if pid and name:
                RETRO_PLAYERS[pid] = name
    print(f"LOADED {len(RETRO_PLAYERS)} RETROSHEET PLAYERS")
else:
    print("WARNING: biofile0.csv not found, old boxscores will be skipped")

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
    home_team = game.get("home_team", "") or game.get("home_code", "")
    away_team = game.get("away_team", "") or game.get("away_code", "")

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

            for pid, pdata in home.get("players", {}).items():
                person = pdata.get("person", {})
                stats = pdata.get("stats", {}).get("batting", {})
                player = person.get("fullName")
                add_game(players, player, {
                    "date": date, "season": season,
                    "team": home_team, "opponent": away_team,
                    "AB": stats.get("atBats", 0),
                    "R": stats.get("runs", 0),
                    "H": stats.get("hits", 0),
                    "RBI": stats.get("rbi", 0),
                    "HR": stats.get("homeRuns", 0),
                    "BB": stats.get("baseOnBalls", 0),
                    "SO": stats.get("strikeOuts", 0)
                })

            for pid, pdata in away.get("players", {}).items():
                person = pdata.get("person", {})
                stats = pdata.get("stats", {}).get("batting", {})
                player = person.get("fullName")
                add_game(players, player, {
                    "date": date, "season": season,
                    "team": away_team, "opponent": home_team,
                    "AB": stats.get("atBats", 0),
                    "R": stats.get("runs", 0),
                    "H": stats.get("hits", 0),
                    "RBI": stats.get("rbi", 0),
                    "HR": stats.get("homeRuns", 0),
                    "BB": stats.get("baseOnBalls", 0),
                    "SO": stats.get("strikeOuts", 0)
                })

        except Exception as e:
            print(f"FAILED RAW {file}: {e}")

    # ==================================================
    # OLD STRUCTURE (home_batting / away_batting arrays)
    # ==================================================

    elif "home_batting" in game or "away_batting" in game:

        try:
            for p in game.get("home_batting", []):
                add_game(players, p.get("player"), {
                    "date": date, "season": season,
                    "team": home_team, "opponent": away_team,
                    "AB": p.get("AB", 0), "R": p.get("R", 0),
                    "H": p.get("H", 0), "RBI": p.get("RBI", 0),
                    "HR": p.get("HR", 0), "BB": p.get("BB", 0),
                    "SO": p.get("SO", 0)
                })
            for p in game.get("away_batting", []):
                add_game(players, p.get("player"), {
                    "date": date, "season": season,
                    "team": away_team, "opponent": home_team,
                    "AB": p.get("AB", 0), "R": p.get("R", 0),
                    "H": p.get("H", 0), "RBI": p.get("RBI", 0),
                    "HR": p.get("HR", 0), "BB": p.get("BB", 0),
                    "SO": p.get("SO", 0)
                })
        except Exception:
            continue

    # ==================================================
    # RETROSHEET EVENT FORMAT
    # ==================================================

    elif "events" in game:

        if not RETRO_PLAYERS:
            continue

        try:
            seen_batters = {"home": set(), "away": set()}

            for event in game.get("events", []):
                if not isinstance(event, list) or event[0] != "play":
                    continue

                # [play, inning, half, batter_id, count, pitches, result]
                half = event[2]       # "0" = away batting, "1" = home batting
                batter_id = event[3]

                side = "away" if half == "0" else "home"
                team = away_team if side == "away" else home_team
                opponent = home_team if side == "away" else away_team

                name = RETRO_PLAYERS.get(batter_id)
                if not name:
                    continue

                if batter_id not in seen_batters[side]:
                    seen_batters[side].add(batter_id)
                    add_game(players, name, {
                        "date": date, "season": season,
                        "team": team, "opponent": opponent,
                        "AB": 0, "R": 0, "H": 0,
                        "RBI": 0, "HR": 0, "BB": 0, "SO": 0
                    })

        except Exception as e:
            print(f"FAILED RETRO {file}: {e}")

# ======================================================
# BUILD PLAYER FILES
# ======================================================

count = 0

for player_name, games in players.items():

    slug = slugify(player_name)

    games.sort(key=lambda x: x.get("date", ""), reverse=True)

    totals = {"games": len(games), "AB": 0, "R": 0, "H": 0,
              "RBI": 0, "HR": 0, "BB": 0, "SO": 0}

    for g in games:
        totals["AB"] += int(g.get("AB", 0) or 0)
        totals["R"]  += int(g.get("R", 0) or 0)
        totals["H"]  += int(g.get("H", 0) or 0)
        totals["RBI"] += int(g.get("RBI", 0) or 0)
        totals["HR"] += int(g.get("HR", 0) or 0)
        totals["BB"] += int(g.get("BB", 0) or 0)
        totals["SO"] += int(g.get("SO", 0) or 0)

    avg = totals["H"] / totals["AB"] if totals["AB"] else 0
    totals["AVG"] = f"{avg:.3f}"

    out = {
        "name": player_name,
        "slug": slug,
        "career": totals,
        "games": games
    }

    with open(f"{PLAYERS_DIR}/{slug}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    count += 1

print(f"BUILT {count} PLAYER FILES")

# ======================================================
# BUILD PLAYERS INDEX
# ======================================================

index = sorted(
    [{"name": name, "player_id": slugify(name)} for name in players.keys()],
    key=lambda x: x["name"]
)

with open(f"{BASE}/players.json", "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False)

print(f"BUILT INDEX WITH {len(index)} PLAYERS")
