import requests
import json
import os
from datetime import datetime, timedelta

BASE_DIR = "docs/data/baseball"
SEASON = "2026"

SEASON_FILE = f"{BASE_DIR}/seasons/{SEASON}.json"
BOXSCORE_DIR = f"{BASE_DIR}/boxscores/{SEASON}"

os.makedirs(BOXSCORE_DIR, exist_ok=True)

# -------------------------
# LOAD EXISTING DATA (SAFE)
# -------------------------
if os.path.exists(SEASON_FILE):
    with open(SEASON_FILE) as f:
        season_data = json.load(f)
else:
    season_data = {"season": SEASON, "games": []}

existing_ids = {g["game_id"] for g in season_data["games"]}

# -------------------------
# DATE RANGE (FIXED)
# -------------------------
start_date = datetime(2026, 3, 1)   # 🔥 start BEFORE your gap
end_date = datetime.now()

print("Fetching games from", start_date.date(), "to", end_date.date())

# -------------------------
# FETCH SCHEDULE
# -------------------------
url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date.date()}&endDate={end_date.date()}"

res = requests.get(url)
data = res.json()

added = 0

for date in data.get("dates", []):
    for game in date.get("games", []):

        game_id = str(game.get("gamePk"))

        # only regular + postseason
        game_type = game.get("gameType")
        if game_type not in ["R", "P"]:
            continue

        # skip if already exists
        if game_id in existing_ids:
            continue

        teams = game.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})

        game_obj = {
            "game_id": game_id,
            "date": game.get("gameDate", "")[:10],
            "game_type": "Regular Season" if game_type == "R" else "Postseason",
            "home_team": home.get("team", {}).get("name", ""),
            "away_team": away.get("team", {}).get("name", ""),
            "home_score": home.get("score", 0),
            "away_score": away.get("score", 0),
            "venue": game.get("venue", {}).get("name", "")
        }

        season_data["games"].append(game_obj)
        added += 1

print(f"Added {added} new games")

# -------------------------
# SAVE SEASON FILE
# -------------------------
with open(SEASON_FILE, "w") as f:
    json.dump(season_data, f, indent=2)

print("Season file updated")
