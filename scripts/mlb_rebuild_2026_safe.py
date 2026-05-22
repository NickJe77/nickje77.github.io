import requests
import json
import os

BASE_DIR = "docs/data/baseball"
SEASON = "2026"

SEASON_FILE = f"{BASE_DIR}/seasons/{SEASON}.json"
BOXSCORE_DIR = f"{BASE_DIR}/boxscores/{SEASON}"

os.makedirs(BOXSCORE_DIR, exist_ok=True)

TEAM_ID_MAP = {
    109: "ARI",
    144: "ATL",
    110: "BAL",
    111: "BOS",
    112: "CHC",
    145: "CHW",
    113: "CIN",
    114: "CLE",
    115: "COL",
    116: "DET",
    117: "HOU",
    118: "KAN",
    108: "LAA",
    119: "LAD",
    146: "MIA",
    158: "MIL",
    142: "MIN",
    121: "NYM",
    147: "NYY",
    133: "ATH",
    143: "PHI",
    134: "PIT",
    135: "SD",
    136: "SEA",
    137: "SF",
    138: "STL",
    139: "TB",
    140: "TEX",
    141: "TOR",
    120: "WSH"
}

print("Downloading MLB 2026 schedule...")

schedule_url = (
    f"https://statsapi.mlb.com/api/v1/schedule?"
    f"sportId=1&season={SEASON}"
)

schedule_data = requests.get(schedule_url).json()

season_games = []

for date_block in schedule_data.get("dates", []):

    game_date = date_block.get("date")

    for game in date_block.get("games", []):

        try:

            game_pk = game.get("gamePk")

            home = game["teams"]["home"]
            away = game["teams"]["away"]

            home_team = home["team"]["name"]
            away_team = away["team"]["name"]

            home_id = home["team"]["id"]
            away_id = away["team"]["id"]

            home_code = TEAM_ID_MAP.get(home_id, "UNK")
            away_code = TEAM_ID_MAP.get(away_id, "UNK")

            venue = (
                game.get("venue", {})
                .get("name", "")
            )

            status = (
                game.get("status", {})
                .get("detailedState", "")
            )

            # -------------------------
            # LIVE DATA
            # -------------------------

            live_url = (
                f"https://statsapi.mlb.com/api/v1.1/game/"
                f"{game_pk}/feed/live"
            )

            live_data = requests.get(live_url).json()

            # -------------------------
            # DEBUG (remove once scores look correct)
            # -------------------------

            print(f"  [{status}] {away_team} @ {home_team}")
            linescore_check = live_data.get("liveData", {}).get("linescore", {})
            home_runs_raw = linescore_check.get("teams", {}).get("home", {}).get("runs", "MISSING")
            away_runs_raw = linescore_check.get("teams", {}).get("away", {}).get("runs", "MISSING")
            print(f"  liveData linescore runs — home: {home_runs_raw}, away: {away_runs_raw}")

            # -------------------------
            # SCORES
            # -------------------------

            home_score = 0
            away_score = 0

            try:
                linescore = live_data["liveData"]["linescore"]
                home_score = linescore["teams"]["home"].get("runs", 0) or 0
                away_score = linescore["teams"]["away"].get("runs", 0) or 0

            except (KeyError, TypeError) as e:
                print(f"  liveData score parse failed: {e}, falling back to schedule data")
                try:
                    home_score = home.get("score", 0) or 0
                    away_score = away.get("score", 0) or 0
                except (KeyError, TypeError) as e2:
                    print(f"  Schedule score parse also failed: {e2}, defaulting to 0-0")

            # -------------------------
            # FILENAME
            # -------------------------

            filename = (
                f"{game_date}_{away_code}_{home_code}.json"
            )

            filepath = os.path.join(
                BOXSCORE_DIR,
                filename
            )

            # -------------------------
            # GAME JSON
            # -------------------------

            game_json = {
                "game_id": game_pk,
                "date": game_date,
                "status": status,
                "venue": venue,

                "home_team": {
                    "name": home_team,
                    "code": home_code,
                    "score": home_score
                },

                "away_team": {
                    "name": away_team,
                    "code": away_code,
                    "score": away_score
                },

                "liveData": live_data.get(
                    "liveData",
                    {}
                )
            }

            # -------------------------
            # SAVE BOXSCORE
            # -------------------------

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    game_json,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print(f"  Saved {filename} ({away_score}-{home_score})")

            # -------------------------
            # SEASON ENTRY
            # -------------------------

            season_games.append({
                "game_id": game_pk,
                "date": game_date,

                "home_team": home_team,
                "away_team": away_team,

                "home_code": home_code,
                "away_code": away_code,

                "home_score": home_score,
                "away_score": away_score,

                "venue": venue,
                "status": status,

                "game_file": filename
            })

        except Exception as e:
            print(f"FAILED game {game.get('gamePk', '?')}: {e}")

# -------------------------
# SORT
# -------------------------

season_games.sort(
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
        season_games,
        f,
        ensure_ascii=False,
        indent=2
    )

print("")
print("DONE")
print(f"Saved {len(season_games)} games")
