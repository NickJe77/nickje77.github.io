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

session = requests.Session()

games = []

def fetch_json(url, retries=5):

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

        wait = 5 + (attempt * 5)

        print(f"Retrying in {wait}s")

        time.sleep(wait)

    return None

start_date = datetime(2025, 10, 1)
end_date = datetime.now()

current = start_date

while current <= end_date:

    ymd = current.strftime("%Y%m%d")

    print(f"\nFETCHING {ymd}")

    scoreboard_url = (
        "https://cdn.nba.com/static/json/liveData/scoreboard/"
        f"todaysScoreboard_{ymd}.json"
    )

    data = fetch_json(scoreboard_url)

    if not data:
        current += timedelta(days=1)
        continue

    rows = (
        data.get("scoreboard", {})
        .get("games", [])
    )

    print(f"GAMES FOUND: {len(rows)}")

    for row in rows:

        try:

            game_id = str(row.get("gameId"))

            if not game_id:
                continue

            game_file = f"{game_id}.json"

            home_team = (
                row.get("homeTeam", {})
                .get("teamName", "")
            )

            away_team = (
                row.get("awayTeam", {})
                .get("teamName", "")
            )

            games.append({
                "game_id": game_id,
                "game_file": game_file,
                "home_team": home_team,
                "away_team": away_team,
                "date": current.strftime("%Y-%m-%d")
            })

            boxscore_url = (
                "https://cdn.nba.com/static/json/liveData/boxscore/"
                f"boxscore_{game_id}.json"
            )

            box_data = fetch_json(boxscore_url)

            if not box_data:
                print("FAILED BOX:", game_id)
                continue

            out_path = os.path.join(BOX_DIR, game_file)

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(box_data, f, indent=2)

            print(f"SAVED {game_file}")

            time.sleep(0.4)

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

print("TOTAL UNIQUE GAMES:", len(final_games))

if len(final_games) < 1000:
    raise SystemExit("ABORTED - TOO FEW GAMES")

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(final_games, f, indent=2)

print("\nDONE")
print(f"TOTAL GAMES: {len(final_games)}")
