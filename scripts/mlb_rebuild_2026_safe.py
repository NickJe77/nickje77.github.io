import requests
import json
import os
import time

BASE_DIR = "docs/data/baseball"
SEASON = "2026"

SEASON_FILE = f"{BASE_DIR}/seasons/{SEASON}.json"
BOXSCORE_DIR = f"{BASE_DIR}/boxscores/{SEASON}"

os.makedirs(BOXSCORE_DIR, exist_ok=True)
os.makedirs(f"{BASE_DIR}/seasons", exist_ok=True)

TEAM_ID_MAP = {
    109: "ARI", 144: "ATL", 110: "BAL", 111: "BOS", 112: "CHC",
    145: "CHW", 113: "CIN", 114: "CLE", 115: "COL", 116: "DET",
    117: "HOU", 118: "KC", 108: "LAA", 119: "LAD", 146: "MIA",
    158: "MIL", 142: "MIN", 121: "NYM", 147: "NYY", 133: "ATH",
    143: "PHI", 134: "PIT", 135: "SD", 136: "SEA", 137: "SF",
    138: "STL", 139: "TB", 140: "TEX", 141: "TOR", 120: "WSH"
}

print("Downloading MLB 2026 schedule...")

month_ranges = [
    ("2026-03-25", "2026-03-31"),
    ("2026-04-01", "2026-04-30"),
    ("2026-05-01", "2026-05-31"),
    ("2026-06-01", "2026-06-30"),
    ("2026-07-01", "2026-07-31"),
    ("2026-08-01", "2026-08-31"),
    ("2026-09-01", "2026-09-30"),
    ("2026-10-01", "2026-10-05"),
]

all_dates = {}

for start, end in month_ranges:
    url = (
        f"https://statsapi.mlb.com/api/v1/schedule?"
        f"sportId=1&season={SEASON}&gameType=R"
        f"&startDate={start}&endDate={end}"
    )
    data = requests.get(url).json()
    for date_block in data.get("dates", []):
        all_dates[date_block["date"]] = date_block
    print(f"  {start} to {end}: {len(data.get('dates', []))} dates")

print(f"Total date blocks: {len(all_dates)}")

season_games = []
saved = 0
skipped_exists = 0
skipped_not_final = 0
failed = 0

for date_block in sorted(all_dates.values(), key=lambda x: x["date"]):

    game_date = date_block.get("date")

    for game in date_block.get("games", []):

        if not isinstance(game, dict):
            continue

        try:
            game_pk = game.get("gamePk")
            home = game["teams"]["home"]
            away = game["teams"]["away"]

            if not isinstance(home, dict) or not isinstance(away, dict):
                continue

            home_team = home.get("team", {}).get("name", "UNK")
            away_team = away.get("team", {}).get("name", "UNK")
            home_id = home.get("team", {}).get("id")
            away_id = away.get("team", {}).get("id")

            if not home_id or not away_id:
                continue

            home_code = TEAM_ID_MAP.get(home_id, "UNK")
            away_code = TEAM_ID_MAP.get(away_id, "UNK")

            venue = game.get("venue", {}).get("name", "")
            status = game.get("status", {}).get("detailedState", "")
            abstract_state = game.get("status", {}).get("abstractGameState", "")

            filename = f"{game_date}_{away_code}_{home_code}.json"
            filepath = os.path.join(BOXSCORE_DIR, filename)

            # --- Already on disk: load and add to season_games ---
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    existing = json.load(f)

                if existing.get("status") != "Final":
                    skipped_not_final += 1
                    continue

                skipped_exists += 1
                h = existing["home_team"]
                a = existing["away_team"]

                season_games.append({
                    "game_id": existing["game_id"],
                    "date": existing["date"],
                    "home_team": h["name"] if isinstance(h, dict) else h,
                    "away_team": a["name"] if isinstance(a, dict) else a,
                    "home_code": h.get("code", home_code) if isinstance(h, dict) else home_code,
                    "away_code": a.get("code", away_code) if isinstance(a, dict) else away_code,
                    "home_score": h.get("score", 0) if isinstance(h, dict) else existing.get("home_score", 0),
                    "away_score": a.get("score", 0) if isinstance(a, dict) else existing.get("away_score", 0),
                    "venue": existing.get("venue", venue),
                    "status": existing.get("status", status),
                    "game_file": filename
                })
                continue

            # --- Not on disk: skip if not final ---
            if abstract_state != "Final":
                skipped_not_final += 1
                continue

            # --- Fetch live data ---
            live_url = (
                f"https://statsapi.mlb.com/api/v1.1/game/"
                f"{game_pk}/feed/live"
            )
            live_data = requests.get(live_url).json()
            time.sleep(0.2)

            if not isinstance(live_data, dict) or "liveData" not in live_data:
                print(f"  Unexpected live_data for {game_pk}")
                failed += 1
                continue

            home_score = 0
            away_score = 0

            try:
                linescore = live_data["liveData"]["linescore"]
                home_score = linescore["teams"]["home"].get("runs", 0) or 0
                away_score = linescore["teams"]["away"].get("runs", 0) or 0
            except (KeyError, TypeError):
                try:
                    home_score = home.get("score", 0) or 0
                    away_score = away.get("score", 0) or 0
                except (KeyError, TypeError):
                    pass

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
                "liveData": live_data.get("liveData", {})
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(game_json, f, ensure_ascii=False, indent=2)

            print(f"  Saved {filename} ({away_score}-{home_score})")
            saved += 1

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
            print(f"  FAILED game {game.get('gamePk', '?')}: {e}")
            failed += 1

season_games.sort(key=lambda x: (x["date"], x["away_team"]))

with open(SEASON_FILE, "w", encoding="utf-8") as f:
    json.dump(season_games, f, ensure_ascii=False, indent=2)

print("")
print("DONE")
print(f"  Saved new:        {saved}")
print(f"  Already on disk:  {skipped_exists}")
print(f"  Not final yet:    {skipped_not_final}")
print(f"  Failed:           {failed}")
print(f"  Total in season file: {len(season_games)}")
