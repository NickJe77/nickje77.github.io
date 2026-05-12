import os
import json
import time
import requests
from datetime import datetime, timedelta

SEASON = "2026"

SEASON_DIR = f"docs/data/nba/{SEASON}"
BOX_DIR = f"docs/data/nba/boxscores/{SEASON}"

os.makedirs(SEASON_DIR, exist_ok=True)
os.makedirs(BOX_DIR, exist_ok=True)

INDEX_FILE = f"{SEASON_DIR}/index.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0 Safari/537.36"
    ),
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json"
}

games = []

start_date = datetime(2025, 10, 1)
end_date = datetime.now()

session = requests.Session()

def get_json(url, retries=5):

    for attempt in range(retries):

        try:

            r = session.get(
                url,
                headers=HEADERS,
                timeout=20
            )

            if r.status_code == 200:
                return r.json()

            print("BAD STATUS:", r.status_code)

        except Exception as e:
            print("REQUEST ERROR:", e)

        sleep_time = 5 + (attempt * 5)

        print(f"Retrying in {sleep_time}s")

        time.sleep(sleep_time)

    return None

current = start_date

while current <= end_date:

    date_str = current.strftime("%Y-%m-%d")

    print(f"\nFETCHING {date_str}")

    scoreboard_url = (
        "https://cdn.nba.com/static/json/liveData/scoreboard/"
        f"todaysScoreboard_00.json"
    )

    data = get_json(scoreboard_url)

    if not data:
        current += timedelta(days=1)
        continue

    scoreboard = data.get("scoreboard", {})
    rows = scoreboard.get("games", [])

    print(f"GAMES FOUND: {len(rows)}")

    for row in rows:

        try:

            game_id = str(row.get("gameId"))

            game_date = (
                row.get("gameEt")
                or row.get("gameDateEst")
                or date_str
            )

            home_team = (
                row.get("homeTeam", {})
                .get("teamName", "")
            )

            away_team = (
                row.get("awayTeam", {})
                .get("teamName", "")
            )

            game_file = f"{game_id}.json"

            games.append({
                "game_id": game_id,
                "game_file": game_file,
                "home_team": home_team,
                "away_team": away_team,
                "date": game_date
            })

            boxscore_url = (
                "https://cdn.nba.com/static/json/liveData/boxscore/"
                f"boxscore_{game_id}.json"
            )

            box_data = get_json(boxscore_url)

            if not box_data:
                print("FAILED BOX:", game_id)
                continue

            out_path = os.path.join(BOX_DIR, game_file)

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(box_data, f, indent=2)

            print(f"SAVED {game_file}")

            time.sleep(0.5)

        except Exception as e:
            print("GAME ERROR:", e)

    current += timedelta(days=1)

unique = {}

for g in games:
    unique[g["game_id"]] = g

final_games = list(unique.values())

final_games.sort(
    key=lambda x: (x.get("date", ""), x.get("game_id", ""))
)

if len(final_games) < 10:
    raise SystemExit("ABORTED - TOO FEW GAMES")

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(final_games, f, indent=2)

print("\nDONE")
print("TOTAL GAMES:", len(final_games))
