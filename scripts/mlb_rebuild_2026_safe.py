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
# TEAM ID → CODE
# -------------------------

TEAM_ID_MAP = {
    109:"ARI", 144:"ATL", 110:"BAL", 111:"BOS", 112:"CHC", 145:"CHW",
    113:"CIN", 114:"CLE", 115:"COL", 116:"DET", 117:"HOU", 118:"KAN",
    108:"LAA", 119:"LOS", 146:"MIA", 158:"MIL", 142:"MIN",
    121:"NEW", 147:"NEW",
    133:"ATH",
    143:"PHI", 134:"PIT", 135:"SDN", 136:"SEA", 137:"SFN",
    138:"STL", 139:"TBR", 140:"TEX", 141:"TOR",
    120:"WSN"
}

# -------------------------
# LOAD EXISTING SEASON
# -------------------------

existing_games = []

if os.path.exists(SEASON_FILE):
    try:
        with open(SEASON_FILE, "r", encoding="utf-8") as f:
            existing_games = json.load(f)
    except:
        existing_games = []

existing_map = {}

for g in existing_games:
    if "game_file" in g:
        existing_map[g["game_file"]] = g

# -------------------------
# MLB SCHEDULE API
# -------------------------

url = (
    f"https://statsapi.mlb.com/api/v1/schedule?"
    f"sportId=1&season={SEASON}"
)

print("Downloading MLB schedule...")

data = requests.get(url).json()

games_out = []

# -------------------------
# PROCESS GAMES
# -------------------------

for date_block in data.get("dates", []):

    game_date = date_block.get("date")

    for game in date_block.get("games", []):

        try:

            game_pk = game.get("gamePk")

            status = (
                game.get("status", {})
                .get("detailedState", "")
            )

            home = game["teams"]["home"]
            away = game["teams"]["away"]

            home_id = home["team"]["id"]
            away_id = away["team"]["id"]

            home_code = TEAM_ID_MAP.get(home_id, "UNK")
            away_code = TEAM_ID_MAP.get(away_id, "UNK")

            home_name = home["team"]["name"]
            away_name = away["team"]["name"]

            home_score = home.get("score")
            away_score = away.get("score")

            venue = (
                game.get("venue", {})
                .get("name", "")
            )

            # -------------------------
            # ORIGINAL FILE FORMAT
            # -------------------------

            box_filename = (
                f"{game_date}_{away_code}_{home_code}.json"
            )

            box_file = os.path.join(
                BOXSCORE_DIR,
                box_filename
            )

            # -------------------------
            # BOXSCORE API
            # -------------------------

            live_url = (
                f"https://statsapi.mlb.com/api/v1.1/game/"
                f"{game_pk}/feed/live"
            )

            live_data = requests.get(live_url).json()

            # -------------------------
            # BUILD BOX JSON
            # -------------------------

            game_json = {
                "game_id": game_pk,
                "date": game_date,
                "status": status,
                "venue": venue,

                "home_team": {
                    "code": home_code,
                    "name": home_name,
                    "score": home_score
                },

                "away_team": {
                    "code": away_code,
                    "name": away_name,
                    "score": away_score
                },

                "boxscore": live_data.get("liveData", {})
            }

            # -------------------------
            # SAVE BOX FILE
            # -------------------------

            with open(box_file, "w", encoding="utf-8") as f:
                json.dump(
                    game_json,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print(f"Saved {box_filename}")

            # -------------------------
            # SEASON ENTRY
            # -------------------------

            season_entry = {
                "game_id": game_pk,
                "date": game_date,
                "status": status,

                "home_team": home_name,
                "away_team": away_name,

                "home_code": home_code,
                "away_code": away_code,

                "home_score": home_score,
                "away_score": away_score,

                "venue": venue,

                "game_file": box_filename
            }

            games_out.append(season_entry)

        except Exception as e:
            print("FAILED:", e)

# -------------------------
# SORT
# -------------------------

games_out.sort(
    key=lambda x: (
        x["date"],
        x["away_team"]
    )
)

# -------------------------
# SAVE SEASON FILE
# -------------------------

with open(SEASON_FILE, "w", encoding="utf-8") as f:
    json.dump(
        games_out,
        f,
        ensure_ascii=False,
        indent=2
    )

print("")
print("DONE")
print(f"Saved {len(games_out)} games")
