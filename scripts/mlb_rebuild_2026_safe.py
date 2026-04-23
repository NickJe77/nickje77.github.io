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
# TEAM ID → CODE (LOCKED)
# -------------------------
TEAM_ID_MAP = {
    109:"ARI", 144:"ATL", 110:"BAL", 111:"BOS", 112:"CHC", 145:"CHW",
    113:"CIN", 114:"CLE", 115:"COL", 116:"DET", 117:"HOU", 118:"KAN",
    108:"LAA", 119:"LOS", 146:"MIA", 158:"MIL", 142:"MIN",
    121:"NEW", 147:"NEW",   # Mets / Yankees
    133:"ATH",
    143:"PHI", 134:"PIT",
    135:"SAN", 137:"SAN",   # Padres / Giants
    136:"SEA",
    138:"ST",
    139:"TAM",
    140:"TEX",
    141:"TOR",
    120:"WAS"
}

# -------------------------
# LOAD SEASON
# -------------------------
if os.path.exists(SEASON_FILE):
    with open(SEASON_FILE) as f:
        games_list = json.load(f)
else:
    games_list = []

existing_ids = {str(g.get("game_id")) for g in games_list}

print("Loaded games:", len(existing_ids))

# -------------------------
# FETCH SCHEDULE
# -------------------------
start_date = "2026-03-01"
end_date = datetime.now().strftime("%Y-%m-%d")

url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date}&endDate={end_date}"
data = requests.get(url).json()

added_games = 0
box_written = 0
skipped_invalid = 0

# -------------------------
# LOOP GAMES
# -------------------------
for date in data.get("dates", []):
    for game in date.get("games", []):

        game_id = str(game.get("gamePk"))
        game_type = game.get("gameType")

        if game_type not in ["R", "P"]:
            continue

        date_str = game.get("gameDate", "")[:10]

        teams = game.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})

        home_id = home.get("team", {}).get("id")
        away_id = away.get("team", {}).get("id")

        home_code = TEAM_ID_MAP.get(home_id)
        away_code = TEAM_ID_MAP.get(away_id)

        # 🔒 HARD LOCK — DO NOT WRITE BAD FILES
        if not home_code or not away_code:
            print("❌ SKIPPING (missing team code):", game_id, home_id, away_id)
            skipped_invalid += 1
            continue

        filename = f"{date_str}_{away_code}_{home_code}.json"
        box_path = os.path.join(BOXSCORE_DIR, filename)

        # -------------------------
        # WRITE BOXSCORE
        # -------------------------
        if not os.path.exists(box_path):

            try:
                feed_url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
                r = requests.get(feed_url)

                if r.status_code != 200:
                    print("❌ FAILED:", filename, r.status_code)
                    continue

                feed = r.json()

                if "liveData" not in feed:
                    print("❌ EMPTY:", filename)
                    continue

                with open(box_path, "w") as f:
                    json.dump(feed, f)

                print("✅ WROTE:", filename)
                box_written += 1

            except Exception as e:
                print("❌ ERROR:", filename, str(e))

        # -------------------------
        # ADD TO SEASON FILE
        # -------------------------
        if game_id not in existing_ids:

            game_obj = {
                "game_id": game_id,
                "date": date_str,
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
# SAVE
# -------------------------
with open(SEASON_FILE, "w") as f:
    json.dump(games_list, f, indent=2)

# -------------------------
# SUMMARY
# -------------------------
print("================================")
print("Games added:", added_games)
print("Boxscores written:", box_written)
print("Skipped invalid:", skipped_invalid)
print("================================")
