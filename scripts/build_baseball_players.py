import os
import json
import glob
from collections import defaultdict

BASE = "docs/data/baseball"

SEASONS_DIR = f"{BASE}/seasons"
PLAYERS_DIR = f"{BASE}/players"

os.makedirs(PLAYERS_DIR, exist_ok=True)

# -------------------------
# CLEAN PLAYER NAME
# -------------------------

def clean_name(name):
    if not name:
        return None

    name = str(name).strip()

    if name.lower() in ["team", "totals"]:
        return None

    return name


# -------------------------
# PLAYER SLUG
# -------------------------

def slugify(name):
    return (
        name.lower()
        .replace(".", "")
        .replace("'", "")
        .replace(",", "")
        .replace(" jr", "-jr")
        .replace(" sr", "-sr")
        .replace(" ", "-")
    )


# -------------------------
# CAREER TOTALS
# -------------------------

def build_totals(games):

    totals = {
        "games": 0,
        "AB": 0,
        "H": 0,
        "HR": 0
    }

    for g in games:

        totals["games"] += 1
        totals["AB"] += int(g.get("AB", 0) or 0)
        totals["H"] += int(g.get("H", 0) or 0)
        totals["HR"] += int(g.get("HR", 0) or 0)

    avg = (
        totals["H"] / totals["AB"]
        if totals["AB"] else 0
    )

    totals["AVG"] = f"{avg:.3f}"

    return totals


# -------------------------
# PLAYER STORAGE
# -------------------------

players = defaultdict(list)

# -------------------------
# LOAD ALL SEASONS
# -------------------------

season_files = sorted(
    glob.glob(f"{SEASONS_DIR}/*.json")
)

print(f"FOUND {len(season_files)} SEASON FILES")

for season_file in season_files:

    print(f"\nPROCESSING {season_file}")

    try:
        with open(season_file, "r", encoding="utf-8") as f:
            season_games = json.load(f)

    except Exception as e:
        print(f"FAILED TO LOAD {season_file}")
        print(e)
        continue

    if not isinstance(season_games, list):
        print("NOT A LIST")
        continue

    for game in season_games:

        season = str(
            game.get("season", "")
        )

        date = game.get("date", "")

        home_team = (
            game.get("home_team")
            or game.get("home")
            or ""
        )

        away_team = (
            game.get("away_team")
            or game.get("away")
            or ""
        )

        # -------------------------
        # HOME BATTERS
        # -------------------------

        home_batters = (
            game.get("home_batting")
            or game.get("homeBatting")
            or []
        )

        for p in home_batters:

            player = clean_name(
                p.get("player")
            )

            if not player:
                continue

            players[player].append({

                "date": date,
                "season": season,
                "team": home_team,
                "opponent": away_team,

                "AB": int(p.get("AB", 0) or 0),
                "H": int(p.get("H", 0) or 0),
                "HR": int(p.get("HR", 0) or 0)

            })

        # -------------------------
        # AWAY BATTERS
        # -------------------------

        away_batters = (
            game.get("away_batting")
            or game.get("awayBatting")
            or []
        )

        for p in away_batters:

            player = clean_name(
                p.get("player")
            )

            if not player:
                continue

            players[player].append({

                "date": date,
                "season": season,
                "team": away_team,
                "opponent": home_team,

                "AB": int(p.get("AB", 0) or 0),
                "H": int(p.get("H", 0) or 0),
                "HR": int(p.get("HR", 0) or 0)

            })


# -------------------------
# BUILD PLAYER FILES
# -------------------------

count = 0

for player_name, games in players.items():

    slug = slugify(player_name)

    # SORT NEWEST FIRST
    games.sort(
        key=lambda x: x.get("date", ""),
        reverse=True
    )

    player_json = {

        "name": player_name,
        "slug": slug,
        "career": build_totals(games),
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
