import os
import csv
import json
import glob
import shutil
import subprocess
import requests
from collections import defaultdict

BASE = "docs/data/baseball"
BOX_DIR = f"{BASE}/boxscores"
PLAYERS_DIR = f"{BASE}/players"
EVENTS_DIR = f"{BASE}/events"

# ROOT CAUSE FIX: the scraper (mlb_rebuild_2026_safe.py) writes box scores
# straight to R2, not to this git-local BOX_DIR at all -- see that script's
# own docstring ("writes straight to R2 instead of docs/data/baseball/ in
# git"). This script previously only ever globbed BOX_DIR, so any season
# scraped after that change (2026 onward) was invisible to it: individual
# game pages (baseball-game.html) fetch straight from R2 and worked fine,
# but this aggregation script never saw those games at all, so player
# stats were silently missing while scores kept working. Fixed by also
# pulling box scores directly from the same public R2 bucket, using each
# season's index file (which lists every game's filename) to know what to
# fetch -- no R2 credentials needed, same public URL the game page uses.
R2_PUBLIC = "https://pub-68c8b4322a9d4d7f9b875047b45ac7c6.r2.dev"
R2_SEASON_RANGE = range(2015, 2028)  # generously covers any season the scraper might have run for


def fetch_r2_json(path):
    try:
        r = requests.get(f"{R2_PUBLIC}/{path}", timeout=15)
        if r.status_code != 200:
            return None
        return r.json()
    except (requests.RequestException, ValueError):
        return None

# Clean and recreate players dir
if os.path.exists(PLAYERS_DIR):
    shutil.rmtree(PLAYERS_DIR)
os.makedirs(PLAYERS_DIR)

# ======================================================
# REASSEMBLE AND EXTRACT EVENT FILES
# ======================================================

parts = sorted(glob.glob(f"{BASE}/boxes.zip.part*"))

if parts:
    print(f"REASSEMBLING {len(parts)} PARTS...")
    zip_path = f"{BASE}/boxes.zip"
    with open(zip_path, "wb") as out:
        for part in parts:
            with open(part, "rb") as f:
                out.write(f.read())
    os.makedirs(EVENTS_DIR, exist_ok=True)
    subprocess.run(["unzip", "-o", zip_path, "-d", EVENTS_DIR], check=True)
    os.remove(zip_path)
    print("EXTRACTED EVENT FILES")

# ======================================================
# TEAM MAP
# ======================================================

TEAM_MAP = {
    "ARI":"Arizona Diamondbacks",
    "ATL":"Atlanta Braves",
    "BAL":"Baltimore Orioles",
    "BOS":"Boston Red Sox",
    "CHC":"Chicago Cubs",
    "CHN":"Chicago Cubs",
    "CHW":"Chicago White Sox",
    "CHA":"Chicago White Sox",
    "CIN":"Cincinnati Reds",
    "CLE":"Cleveland Guardians",
    "COL":"Colorado Rockies",
    "DET":"Detroit Tigers",
    "HOU":"Houston Astros",
    "KC":"Kansas City Royals",
    "KCA":"Kansas City Royals",
    "LAA":"Los Angeles Angels",
    "ANA":"Los Angeles Angels",
    "CAL":"California Angels",
    "LAD":"Los Angeles Dodgers",
    "LAN":"Los Angeles Dodgers",
    "MIA":"Miami Marlins",
    "FLO":"Florida Marlins",
    "MIL":"Milwaukee Brewers",
    "MLN":"Milwaukee Braves",
    "MIN":"Minnesota Twins",
    "NYM":"New York Mets",
    "NYN":"New York Mets",
    "NYY":"New York Yankees",
    "NYA":"New York Yankees",
    "ATH":"Athletics",
    "OAK":"Athletics",
    "PHA":"Philadelphia Athletics",
    "PHI":"Philadelphia Phillies",
    "PIT":"Pittsburgh Pirates",
    "SD":"San Diego Padres",
    "SDN":"San Diego Padres",
    "SEA":"Seattle Mariners",
    "SF":"San Francisco Giants",
    "SFN":"San Francisco Giants",
    "STL":"St Louis Cardinals",
    "SLN":"St Louis Cardinals",
    "TB":"Tampa Bay Rays",
    "TBA":"Tampa Bay Rays",
    "TEX":"Texas Rangers",
    "TOR":"Toronto Blue Jays",
    "WSH":"Washington Nationals",
    "WAS":"Washington Nationals",
    "MON":"Montreal Expos",
    "BRO":"Brooklyn Dodgers",
    "BSN":"Boston Braves",
    "NY1":"New York Giants",
    "SLA":"St Louis Browns",
    "WS1":"Washington Senators",
    "WS2":"Washington Senators",
    "KC1":"Kansas City Athletics",
    "SE1":"Seattle Pilots",
    "CL4":"Cleveland Spiders",
    "LS3":"Louisville Colonels",
    "RC1":"Rochester Broncos",
    "BLN":"Baltimore Orioles",
    "CLE":"Cleveland Guardians",
}

# ======================================================
# RETROSHEET PLAYER ID LOOKUP
# ======================================================

RETRO_PLAYERS = {}

biofile_path = f"{BASE}/biofile0.csv"

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
# PARSE EVENT FILES - only EBN (National) OR EBA (American)
# to avoid duplicates. We use both but deduplicate by game_id + player
# ======================================================

event_files = glob.glob(f"{EVENTS_DIR}/boxes/*.[Ee][Bb][AaNn]")
print(f"FOUND {len(event_files)} EVENT FILES")

# Track game+player combos to avoid duplicates from EBA+EBN overlap
seen = set()

for ef in event_files:
    try:
        current_game = {}
        with open(ef, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                parts_line = line.split(",")

                if parts_line[0] == "id":
                    current_game = {"id": parts_line[1]}

                elif parts_line[0] == "info":
                    if parts_line[1] == "date":
                        current_game["date"] = parts_line[2].replace("/", "-")
                    elif parts_line[1] == "visteam":
                        current_game["away"] = parts_line[2]
                    elif parts_line[1] == "hometeam":
                        current_game["home"] = parts_line[2]

                elif parts_line[0] == "stat" and parts_line[1] == "bline":
                    if len(parts_line) < 17:
                        continue
                    pid = parts_line[2]
                    side = parts_line[3]
                    seq = parts_line[5]

                    if seq != "1":
                        continue

                    # Deduplicate: same game + same player
                    game_id = current_game.get("id", "")
                    dedup_key = f"{game_id}:{pid}"
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)

                    name = RETRO_PLAYERS.get(pid)
                    if not name:
                        continue

                    team_code = current_game.get("away") if side == "0" else current_game.get("home")
                    opp_code = current_game.get("home") if side == "0" else current_game.get("away")
                    team = TEAM_MAP.get(team_code, team_code)
                    opponent = TEAM_MAP.get(opp_code, opp_code)
                    date = current_game.get("date", "")
                    season = date[:4] if date else ""

                    try:
                        ab  = int(parts_line[6])
                        r   = int(parts_line[7])
                        h   = int(parts_line[8])
                        hr  = int(parts_line[11])
                        rbi = int(parts_line[12])
                        bb  = int(parts_line[16])
                        so  = int(parts_line[18])
                    except (ValueError, IndexError):
                        continue

                    add_game(players, name, {
                        "date": date,
                        "season": season,
                        "team": team,
                        "opponent": opponent,
                        "AB": ab, "R": r, "H": h,
                        "RBI": rbi, "HR": hr, "BB": bb, "SO": so
                    })

    except Exception as e:
        print(f"FAILED EVENT FILE {ef}: {e}")

def process_boxscore_game(game, source_label=""):
    season = str(game.get("season", ""))
    date = game.get("date", "")
    raw_home = game.get("home_team", "") or game.get("home_code", "")
    if isinstance(raw_home, dict): raw_home = raw_home.get("name", "") or raw_home.get("code", "")
    home_team = TEAM_MAP.get(raw_home, raw_home)
    raw_away = game.get("away_team", "") or game.get("away_code", "")
    if isinstance(raw_away, dict): raw_away = raw_away.get("name", "") or raw_away.get("code", "")
    away_team = TEAM_MAP.get(raw_away, raw_away)

    if "liveData" in game:
        try:
            box = game.get("liveData", {}).get("boxscore", {}).get("teams", {})
            for pid, pdata in box.get("home", {}).get("players", {}).items():
                person = pdata.get("person", {})
                stats = pdata.get("stats", {}).get("batting", {})
                player = person.get("fullName")
                add_game(players, player, {
                    "date": date, "season": season,
                    "team": home_team, "opponent": away_team,
                    "AB": stats.get("atBats", 0), "R": stats.get("runs", 0),
                    "H": stats.get("hits", 0), "RBI": stats.get("rbi", 0),
                    "HR": stats.get("homeRuns", 0), "BB": stats.get("baseOnBalls", 0),
                    "SO": stats.get("strikeOuts", 0)
                })
            for pid, pdata in box.get("away", {}).get("players", {}).items():
                person = pdata.get("person", {})
                stats = pdata.get("stats", {}).get("batting", {})
                player = person.get("fullName")
                add_game(players, player, {
                    "date": date, "season": season,
                    "team": away_team, "opponent": home_team,
                    "AB": stats.get("atBats", 0), "R": stats.get("runs", 0),
                    "H": stats.get("hits", 0), "RBI": stats.get("rbi", 0),
                    "HR": stats.get("homeRuns", 0), "BB": stats.get("baseOnBalls", 0),
                    "SO": stats.get("strikeOuts", 0)
                })
        except Exception as e:
            print(f"FAILED {source_label}: {e}")

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
            pass


# ======================================================
# PARSE JSON BOXSCORES -- local git-committed files (historical seasons)
# ======================================================

json_files = glob.glob(f"{BOX_DIR}/**/*.json", recursive=True)
print(f"FOUND {len(json_files)} JSON BOXSCORES (local git)")

for file in json_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            game = json.load(f)
    except Exception:
        continue
    process_boxscore_game(game, source_label=file)

# ======================================================
# PARSE JSON BOXSCORES -- direct from R2 (current/recent seasons the
# scraper writes straight to R2, never to the local git path above)
# ======================================================

r2_game_count = 0
for season_try in R2_SEASON_RANGE:
    index = fetch_r2_json(f"baseball/seasons/{season_try}.json")
    if not index:
        continue
    print(f"R2: season {season_try} index has {len(index)} game(s) listed")
    for entry in index:
        game_file = entry.get("game_file")
        if not game_file:
            continue
        game = fetch_r2_json(f"baseball/boxscores/{season_try}/{game_file}")
        if not game:
            continue
        process_boxscore_game(game, source_label=f"R2:{season_try}/{game_file}")
        r2_game_count += 1

print(f"FOUND {r2_game_count} JSON BOXSCORES (R2)")

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
        totals["AB"]  += int(g.get("AB", 0) or 0)
        totals["R"]   += int(g.get("R", 0) or 0)
        totals["H"]   += int(g.get("H", 0) or 0)
        totals["RBI"] += int(g.get("RBI", 0) or 0)
        totals["HR"]  += int(g.get("HR", 0) or 0)
        totals["BB"]  += int(g.get("BB", 0) or 0)
        totals["SO"]  += int(g.get("SO", 0) or 0)

    avg = totals["H"] / totals["AB"] if totals["AB"] else 0
    totals["AVG"] = f"{avg:.3f}"

    out = {"name": player_name, "slug": slug, "career": totals, "games": games}

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

# ======================================================
# BUILD PER-SEASON LEADER FILES
# ======================================================

SEASONS_DIR = f"{BASE}/season_leaders"
os.makedirs(SEASONS_DIR, exist_ok=True)

# Aggregate stats per player per season
season_data = defaultdict(lambda: defaultdict(lambda: {
    "player_name": "", "player_id": "", "team": "",
    "games": 0, "AB": 0, "R": 0, "H": 0,
    "RBI": 0, "HR": 0, "BB": 0, "SO": 0
}))

for player_name, games in players.items():
    slug = slugify(player_name)
    for g in games:
        season = str(g.get("season", ""))
        if not season:
            continue
        row = season_data[season][slug]
        row["player_name"] = player_name
        row["player_id"] = slug
        row["team"] = g.get("team", "")
        row["games"] += 1
        row["AB"]  += int(g.get("AB", 0) or 0)
        row["R"]   += int(g.get("R", 0) or 0)
        row["H"]   += int(g.get("H", 0) or 0)
        row["RBI"] += int(g.get("RBI", 0) or 0)
        row["HR"]  += int(g.get("HR", 0) or 0)
        row["BB"]  += int(g.get("BB", 0) or 0)
        row["SO"]  += int(g.get("SO", 0) or 0)

for season, season_players in season_data.items():
    out = list(season_players.values())
    with open(f"{SEASONS_DIR}/{season}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

print(f"BUILT {len(season_data)} SEASON FILES")
