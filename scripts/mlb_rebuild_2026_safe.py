import requests
import json
from pathlib import Path
from datetime import datetime
import time
import re

print("MLB 2026 FULL BOX SCORE BUILD")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1.1"

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
BOX_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

INDEX = {}


# -----------------------------
# PLAYER CODE
# -----------------------------
def make_player_code(name):
    name = re.sub(r"[^\w\s]", "", name.lower())
    parts = name.split()
    if len(parts) < 2:
        return "unknown001"
    first = parts[0]
    last = parts[-1]
    return f"{last[:5]}{first[:2]}001"


# -----------------------------
# TEAM CODE
# -----------------------------
def get_team_code(team):
    return (
        team.get("abbreviation")
        or team.get("teamCode")
        or team.get("fileCode")
        or team.get("name", "")[:3].upper()
    )


# -----------------------------
# GET SCHEDULE
# -----------------------------
def get_schedule():
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            if g.get("gameType") not in ["R", "P"]:
                continue

            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["gameDate"][:10],
                "home": get_team_code(g["teams"]["home"]["team"]),
                "away": get_team_code(g["teams"]["away"]["team"])
            })

    print(f"FOUND {len(games)} GAMES")
    return games


# -----------------------------
# BUILD GAME (FULL STATS)
# -----------------------------
def build_game(game):

    game_id = game["game_id"]
    url = f"{BASE}/game/{game_id}/feed/live"

    try:
        data = requests.get(url, headers=HEADERS).json()
    except:
        print("FAILED", game_id)
        return False

    try:
        box = data["liveData"]["boxscore"]["teams"]

        def extract_batting(team):
            out = []
            for p in team["players"].values():
                stats = p.get("stats", {}).get("batting")
                if not stats:
                    continue

                name = p["person"]["fullName"]
                out.append({
                    "player_id": make_player_code(name),
                    "AB": stats.get("atBats", 0),
                    "H": stats.get("hits", 0),
                    "BB": stats.get("baseOnBalls", 0),
                    "SO": stats.get("strikeOuts", 0)
                })
            return out

        def extract_pitching(team):
            out = []
            for p in team["players"].values():
                stats = p.get("stats", {}).get("pitching")
                if not stats:
                    continue

                name = p["person"]["fullName"]
                out.append({
                    "player_id": make_player_code(name),
                    "IP": stats.get("inningsPitched", "0.0"),
                    "H": stats.get("hits", 0),
                    "BB": stats.get("baseOnBalls", 0),
                    "SO": stats.get("strikeOuts", 0)
                })
            return out

        game_json = {
            "game_id": game_id,
            "date": game["date"],
            "season": SEASON,
            "home_code": game["home"],
            "away_code": game["away"],

            # ✅ FULL DATA (THIS FIXES EVERYTHING)
            "batters_home": extract_batting(box["home"]),
            "batters_away": extract_batting(box["away"]),
            "pitchers_home": extract_pitching(box["home"]),
            "pitchers_away": extract_pitching(box["away"])
        }

        file_name = f"{game['date']}_{game['away']}_{game['home']}.json"

        with open(BOX_DIR / file_name, "w") as f:
            json.dump(game_json, f, indent=2)

        INDEX[game_id] = file_name

        print("SAVED", file_name)
        return True

    except Exception as e:
        print("ERROR", game_id, e)
        return False


# -----------------------------
# MAIN
# -----------------------------
games = get_schedule()

for g in games:
    build_game(g)
    time.sleep(0.3)

# INDEX
with open(BOX_DIR / "index.json", "w") as f:
    json.dump(INDEX, f, indent=2)

print("DONE")
