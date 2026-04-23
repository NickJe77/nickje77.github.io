import requests
import json
import os
from datetime import datetime

BASE_DIR = "docs/data/baseball"
SEASON = "2026"

SEASON_FILE = f"{BASE_DIR}/seasons/{SEASON}.json"
BOXSCORE_DIR = f"{BASE_DIR}/boxscores/{SEASON}"

os.makedirs(BOXSCORE_DIR, exist_ok=True)

# -------------------------
# LOAD SEASON DATA
# -------------------------
if os.path.exists(SEASON_FILE):
    with open(SEASON_FILE) as f:
        season_data = json.load(f)
else:
    season_data = []

games_list = season_data if isinstance(season_data, list) else season_data.get("games", [])

existing_ids = {str(g.get("game_id")) for g in games_list}

# -------------------------
# DATE RANGE (FIX GAP)
# -------------------------
start_date = datetime(2026, 3, 1)
end_date = datetime.now()

print("Fetching schedule...")

url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date.date()}&endDate={end_date.date()}"
data = requests.get(url).json()

added_games = 0
new_boxscores = 0

for date in data.get("dates", []):
    for game in date.get("games", []):

        game_id = str(game.get("gamePk"))
        game_type = game.get("gameType")

        if game_type not in ["R", "P"]:
            continue

        # -------------------------
        # BUILD BOXSCORE IF MISSING
        # -------------------------
        box_file = f"{BOXSCORE_DIR}/{game_id}.json"

        if not os.path.exists(box_file):
            feed_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"

            try:
                feed = requests.get(feed_url).json()

                with open(box_file, "w") as f:
                    json.dump(feed, f)

                new_boxscores += 1
                print("Saved boxscore:", game_id)

            except Exception as e:
                print("Failed boxscore:", game_id)
                continue

        # -------------------------
        # ADD TO SEASON FILE
        # -------------------------
        if game_id not in existing_ids:

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

            games_list.append(game_obj)
            added_games += 1

print(f"Added {added_games} games")
print(f"Added {new_boxscores} boxscores")

# -------------------------
# SAVE SEASON FILE
# -------------------------
if isinstance(season_data, dict):
    season_data["games"] = games_list
    output = season_data
else:
    output = games_list

with open(SEASON_FILE, "w") as f:
    json.dump(output, f, indent=2)

print("Done")
