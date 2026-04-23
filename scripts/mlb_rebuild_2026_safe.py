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
# LOAD EXISTING SEASON DATA
# -------------------------
if os.path.exists(SEASON_FILE):
    with open(SEASON_FILE) as f:
        games_list = json.load(f)
else:
    games_list = []

existing_ids = {str(g.get("game_id")) for g in games_list}

print("Loaded existing games:", len(existing_ids))

# -------------------------
# FETCH SCHEDULE (FULL RANGE)
# -------------------------
start_date = "2026-03-01"
end_date = datetime.now().strftime("%Y-%m-%d")

print("Fetching schedule:", start_date, "to", end_date)

url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date}&endDate={end_date}"
data = requests.get(url).json()

added_games = 0
added_boxscores = 0

# -------------------------
# LOOP GAMES
# -------------------------
for date in data.get("dates", []):
    for game in date.get("games", []):

        game_id = str(game.get("gamePk"))
        game_type = game.get("gameType")

        # ONLY REGULAR + POSTSEASON
        if game_type not in ["R", "P"]:
            continue

        status = game.get("status", {}).get("detailedState", "")

        teams = game.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})

        # -------------------------
        # BUILD BOXSCORE (KEY FIX)
        # -------------------------
        box_path = f"{BOXSCORE_DIR}/{game_id}.json"

        if not os.path.exists(box_path):

            if status != "Final":
                print("Skipping (not final):", game_id)
            else:
                feed_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"

                try:
                    r = requests.get(feed_url)

                    if r.status_code != 200:
                        print("Bad response:", game_id, r.status_code)
                    else:
                        feed = r.json()

                        # validate feed
                        if "liveData" not in feed or not feed["liveData"]:
                            print("Empty feed:", game_id)
                        else:
                            with open(box_path, "w") as f:
                                json.dump(feed, f)

                            added_boxscores += 1
                            print("Saved boxscore:", game_id)

                except Exception as e:
                    print("ERROR fetching boxscore:", game_id, str(e))

        # -------------------------
        # ADD TO SEASON FILE
        # -------------------------
        if game_id not in existing_ids:

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
# SORT (FOR YOUR UI)
# -------------------------
games_list.sort(key=lambda x: x["date"])

# -------------------------
# SAVE SEASON FILE
# -------------------------
with open(SEASON_FILE, "w") as f:
    json.dump(games_list, f, indent=2)

# -------------------------
# SUMMARY
# -------------------------
print("===================================")
print("Added games:", added_games)
print("Added boxscores:", added_boxscores)
print("Total games now:", len(games_list))
print("===================================")
