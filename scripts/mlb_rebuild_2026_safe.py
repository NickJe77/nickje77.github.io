import requests
import json
from pathlib import Path
from datetime import datetime
import time
import re
import os

print("MLB 2026 FULL BUILD (FINAL FIX)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1.1"

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
SEASON_FILE = Path(f"docs/data/baseball/seasons/{SEASON}.json")

BOX_DIR.mkdir(parents=True, exist_ok=True)
SEASON_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

INDEX = {}
NEW_PLAYERS = {}
SEASON_GAMES = []

def make_player_code(name):
    name_clean = re.sub(r"[^\w\s]", "", name.lower())
    parts = name_clean.split()
    if len(parts) < 2:
        return "unknown001"
    code = f"{parts[-1][:5]}{parts[0][:2]}001"
    NEW_PLAYERS[code] = name
    return code

def get_team_code(team):
    return (
        team.get("abbreviation")
        or team.get("teamCode")
        or team.get("fileCode")
        or team.get("name", "")[:3].upper()
    )

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
                "home": g["teams"]["home"]["team"],
                "away": g["teams"]["away"]["team"]
            })

    print(f"FOUND {len(games)} GAMES")
    return games

def build_game(game):

    game_id = game["game_id"]
    url = f"{BASE}/game/{game_id}/feed/live"

    data = requests.get(url, headers=HEADERS).json()

    box = data["liveData"]["boxscore"]["teams"]
    linescore = data["liveData"]["linescore"]
    gameData = data["gameData"]

    home_team = game["home"]
    away_team = game["away"]

    home_code = get_team_code(home_team)
    away_code = get_team_code(away_team)

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

    file_name = f"{game['date']}_{away_code}_{home_code}.json"

    with open(BOX_DIR / file_name, "w") as f:
        json.dump({
            "game_id": game_id,
            "date": game["date"],
            "home_code": home_code,
            "away_code": away_code,
            "home_team": home_team.get("name"),
            "away_team": away_team.get("name"),
            "batters_home": extract_batting(box["home"]),
            "batters_away": extract_batting(box["away"]),
            "pitchers_home": extract_pitching(box["home"]),
            "pitchers_away": extract_pitching(box["away"])
        }, f, indent=2)

    os.utime(BOX_DIR / file_name, None)

    INDEX[game_id] = file_name

    SEASON_GAMES.append({
        "game_id": game_id,
        "date": game["date"],
        "home_team": home_team.get("name"),
        "away_team": away_team.get("name"),
        "venue": gameData["venue"]["name"],
        "away_score": linescore["teams"]["away"]["runs"],
        "home_score": linescore["teams"]["home"]["runs"]
    })

games = get_schedule()

for g in games:
    build_game(g)
    time.sleep(0.3)

with open(BOX_DIR / "index.json", "w") as f:
    json.dump(INDEX, f, indent=2)

# 🔥 THIS IS THE CRITICAL FIX
with open(SEASON_FILE, "w") as f:
    json.dump({"games": SEASON_GAMES}, f, indent=2)

print("SEASON FILE FIXED")
