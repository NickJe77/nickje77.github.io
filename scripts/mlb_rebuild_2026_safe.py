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
# LOAD EXISTING SEASON
# -------------------------
if os.path.exists(SEASON_FILE):
    with open(SEASON_FILE) as f:
        games_list = json.load(f)
else:
    games_list = []

existing_ids = {str(g.get("game_id")) for g in games_list}

print("Existing games:", len(existing_ids))

# -------------------------
# FETCH SCHEDULE (FULL RANGE)
# -------------------------
start_date = "2026-03-01"
end_date = datetime.now().strftime("%Y-%m-%d")

print("Fetching schedule:", start_date, "to", end_date)

url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date}&endDate={end_date}"
data = requests.get(url).json()

added_games = 0
box_written = 0

# -------------------------
# LOOP THROUGH GAMES
# -------------------------
for date in data.get("dates", []):
    for game in date.get("games", []):

        game_id = str(game.get("gamePk"))
        game_type = game.get("gameType")

        if game_type not in ["R", "P"]:
            continue

        print("Processing:", game_id)

        # -------------------------
        # FORCE BOXSCORE WRITE
        # -------------------------
        box_path = f"{BOXSCORE_DIR}/{game_id}.json"

        try:
            # 🔥 DIFFERENT ENDPOINT (MORE STABLE)
            url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
            r = requests.get(url)

            if r.status_code != 200:
                print("FAILED:", game_id, r.status_code)
                continue

            data = r.json()

            # 🔥 ALWAYS WRITE (even partial)
            with open(box_path, "w") as f:
                json.dump(data, f)

            box_written += 1
            print("WROTE:", game_id)

        except Exception as e:
            print("ERROR:", game_id, str(e))

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
                "away_team": away.get("team", {}).get("name", ""),
                "home_team": home.get("team", {}).get("name", ""),
                "away_score": away.get("score", None),
                "home_score": home.get("score", None),
                "venue": game.get("venue", {}).get("name", "")
            }

            games_list.append(game_obj)
            added_games += 1

# -------------------------
# SORT
# -------------------------
games_list.sort(key=lambda x: x["date"])

# -------------------------
# SAVE SEASON
# -------------------------
with open(SEASON_FILE, "w") as f:
    json.dump(games_list, f, indent=2)

# -------------------------
# SUMMARY
# -------------------------
print("================================")
print("Games added:", added_games)
print("Boxscores written:", box_written)
print("================================")
