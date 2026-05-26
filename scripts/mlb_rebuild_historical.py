import requests
import json
import os
import time

BASE_DIR = "docs/data/baseball"
START_YEAR = 2008
END_YEAR = 2025

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

for SEASON in range(START_YEAR, END_YEAR + 1):

    print(f"\n{'='*50}")
    print(f"Processing {SEASON}...")
    print(f"{'='*50}")

    SEASON_FILE  = f"{BASE_DIR}/seasons/{SEASON}.json"
    BOXSCORE_DIR = f"{BASE_DIR}/boxscores/{SEASON}"

    os.makedirs(BOXSCORE_DIR, exist_ok=True)

    try:
        schedule_url = (
            f"https://statsapi.mlb.com/api/v1/schedule?"
            f"sportId=1&season={SEASON}&gameType=R"
        )
        schedule_data = requests.get(schedule_url, timeout=30).json()
    except Exception as e:
        print(f"  ERROR fetching schedule for {SEASON}: {e}")
        continue

    season_games = []
    total = sum(len(d.get("games", [])) for d in schedule_data.get("dates", []))
    print(f"  Found {total} games")

    for date_block in schedule_data.get("dates", []):

        game_date = date_block.get("date")

        for game in date_block.get("games", []):

            try:

                game_pk   = game.get("gamePk")
                home      = game["teams"]["home"]
                away      = game["teams"]["away"]
                home_team = home["team"]["name"]
                away_team = away["team"]["name"]
                home_id   = home["team"]["id"]
                away_id   = away["team"]["id"]
                home_code = TEAM_ID_MAP.get(home_id, "UNK")
                away_code = TEAM_ID_MAP.get(away_id, "UNK")
                venue     = game.get("venue", {}).get("name", "")
                status    = game.get("status", {}).get("detailedState", "")

                live_url  = (
                    f"https://statsapi.mlb.com/api/v1.1/game/"
                    f"{game_pk}/feed/live"
                )
                live_data = requests.get(live_url, timeout=30).json()

                home_score = 0
                away_score = 0

                try:
                    linescore  = live_data["liveData"]["linescore"]
                    home_score = linescore["teams"]["home"].get("runs", 0) or 0
                    away_score = linescore["teams"]["away"].get("runs", 0) or 0
                except (KeyError, TypeError):
                    try:
                        home_score = home.get("score", 0) or 0
                        away_score = away.get("score", 0) or 0
                    except (KeyError, TypeError):
                        pass

                filename = f"{game_date}_{away_code}_{home_code}.json"
                filepath = os.path.join(BOXSCORE_DIR, filename)

                game_json = {
                    "game_id":   game_pk,
                    "date":      game_date,
                    "status":    status,
                    "venue":     venue,
                    "home_team": {
                        "name":  home_team,
                        "code":  home_code,
                        "score": home_score
                    },
                    "away_team": {
                        "name":  away_team,
                        "code":  away_code,
                        "score": away_score
                    },
                    "liveData": live_data.get("liveData", {})
                }

                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(game_json, f, ensure_ascii=False, indent=2)

                season_games.append({
                    "game_id":    game_pk,
                    "date":       game_date,
                    "home_team":  home_team,
                    "away_team":  away_team,
                    "home_code":  home_code,
                    "away_code":  away_code,
                    "home_score": home_score,
                    "away_score": away_score,
                    "venue":      venue,
                    "status":     status,
                    "game_file":  filename
                })

                time.sleep(0.1)

            except Exception as e:
                print(f"  FAILED game {game.get('gamePk', '?')}: {e}")

    season_games.sort(key=lambda x: (x["date"], x["away_team"]))

    with open(SEASON_FILE, "w", encoding="utf-8") as f:
        json.dump(season_games, f, ensure_ascii=False, indent=2)

    print(f"  Saved {len(season_games)} games")
    time.sleep(1)

print("\nALL DONE")
