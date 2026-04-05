import requests
import json
from pathlib import Path
from datetime import datetime
import time

print("MLB 2026 SAFE REBUILD STARTING")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1.1"

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
BOX_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# -------------------------------------------------
# GET SCHEDULE
# -------------------------------------------------
def get_schedule():
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):
            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["gameDate"][:10]
            })

    print(f"Found {len(games)} games")
    return games


# -------------------------------------------------
# GET GAME DATA
# -------------------------------------------------
def get_game(game_id):
    url = f"{BASE}/game/{game_id}/feed/live"

    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        data = res.json()
    except:
        print(f"Failed to load game {game_id}")
        return None

    try:
        gameData = data["gameData"]
        liveData = data["liveData"]

        home = gameData["teams"]["home"]["name"]
        away = gameData["teams"]["away"]["name"]
        venue = gameData["venue"]["name"]

        box = liveData["boxscore"]["teams"]

        def extract_team(team):
            players = []
            batting = []
            pitching = []

            for p_id, p in team["players"].items():
                person = p["person"]["fullName"]

                stats = p.get("stats", {})

                bat = stats.get("batting", {})
                pit = stats.get("pitching", {})

                if bat:
                    batting.append({
                        "player": person,
                        "AB": bat.get("atBats", 0),
                        "R": bat.get("runs", 0),
                        "H": bat.get("hits", 0),
                        "RBI": bat.get("rbi", 0)
                    })

                if pit:
                    pitching.append({
                        "player": person,
                        "IP": pit.get("inningsPitched", "0.0"),
                        "H": pit.get("hits", 0),
                        "ER": pit.get("earnedRuns", 0),
                        "SO": pit.get("strikeOuts", 0)
                    })

            return {
                "batting": batting,
                "pitching": pitching
            }

        game_json = {
            "game_id": game_id,
            "season": SEASON,
            "date": gameData["datetime"]["originalDate"],
            "venue": venue,
            "teams": {
                "home": home,
                "away": away
            },
            "boxscore": {
                "home": extract_team(box["home"]),
                "away": extract_team(box["away"])
            }
        }

        return game_json

    except Exception as e:
        print(f"Parse error {game_id}: {e}")
        return None


# -------------------------------------------------
# MAIN
# -------------------------------------------------
games = get_schedule()

count = 0

for g in games:
    game_id = g["game_id"]

    file_path = BOX_DIR / f"{game_id}.json"

    if file_path.exists():
        continue

    game_data = get_game(game_id)

    if game_data:
        with open(file_path, "w") as f:
            json.dump(game_data, f, indent=2)

        count += 1
        print(f"Saved {game_id}")

    time.sleep(0.5)

print(f"DONE — {count} games saved")
