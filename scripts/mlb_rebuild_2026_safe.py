import requests
import json
from pathlib import Path
from datetime import datetime
import time
import re

print("MLB 2026 FULL BUILD (SAFE)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1.1"

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
BOX_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

INDEX = {}
NEW_PLAYERS = {}

# -----------------------------
# PLAYER CODE (SAFE)
# -----------------------------
def make_player_code(name):
    name_clean = re.sub(r"[^\w\s]", "", name.lower())
    parts = name_clean.split()

    if len(parts) < 2:
        return "unknown001"

    first = parts[0]
    last = parts[-1]

    code = f"{last[:5]}{first[:2]}001"

    # only store NEW players (do not overwrite existing)
    NEW_PLAYERS[code] = name

    return code

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

            home = g["teams"]["home"]["team"]
            away = g["teams"]["away"]["team"]

            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["gameDate"][:10],
                "home_code": get_team_code(home),
                "away_code": get_team_code(away),
                "home_team": home.get("name"),
                "away_team": away.get("name")
            })

    print(f"FOUND {len(games)} GAMES")
    return games

# -----------------------------
# BUILD GAME
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
                code = make_player_code(name)

                out.append({
                    "player_id": code,
                    "AB": stats.get("atBats", 0),
                    "R": stats.get("runs", 0),
                    "H": stats.get("hits", 0),
                    "RBI": stats.get("rbi", 0),
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
                code = make_player_code(name)

                out.append({
                    "player_id": code,
                    "IP": stats.get("inningsPitched", "0.0"),
                    "H": stats.get("hits", 0),
                    "R": stats.get("runs", 0),
                    "ER": stats.get("earnedRuns", 0),
                    "BB": stats.get("baseOnBalls", 0),
                    "SO": stats.get("strikeOuts", 0)
                })
            return out

        game_json = {
            "game_id": game_id,
            "date": game["date"],
            "season": SEASON,
            "home_code": game["home_code"],
            "away_code": game["away_code"],
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "batters_home": extract_batting(box["home"]),
            "batters_away": extract_batting(box["away"]),
            "pitchers_home": extract_pitching(box["home"]),
            "pitchers_away": extract_pitching(box["away"])
        }

        file_name = f"{game['date']}_{game['away_code']}_{game['home_code']}.json"

        with open(BOX_DIR / file_name, "w") as f:
            json.dump(game_json, f, indent=2)

        INDEX[game_id] = file_name

        print("SAVED", file_name)
        return True

    except Exception as e:
        print("ERROR", game_id, e)
        return False

# -----------------------------
# RUN
# -----------------------------
games = get_schedule()

for g in games:
    build_game(g)
    time.sleep(0.3)

# -----------------------------
# SAVE INDEX
# -----------------------------
with open(BOX_DIR / "index.json", "w") as f:
    json.dump(INDEX, f, indent=2)

# -----------------------------
# SAFE PLAYER MERGE (KEY FIX)
# -----------------------------
players_path = Path("docs/data/baseball/players.json")

existing = {}

if players_path.exists():
    with open(players_path) as f:
        data = json.load(f)
        for p in data:
            existing[p["player_id"]] = p["name"]

# ONLY ADD NEW — NEVER REMOVE
for k, v in NEW_PLAYERS.items():
    if k not in existing:
        existing[k] = v

players_list = [
    {"player_id": k, "name": v}
    for k, v in sorted(existing.items())
]

with open(players_path, "w") as f:
    json.dump(players_list, f, indent=2)

print(f"PLAYERS TOTAL: {len(players_list)}")
print("DONE")
