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
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json"
}

games = []

start_date = datetime(2025, 10, 1)
end_date = datetime.now()

current = start_date

while current <= end_date:

    game_date = current.strftime("%m/%d/%Y")

    print(f"\nFETCHING {game_date}")

    scoreboard_url = (
        "https://stats.nba.com/stats/scoreboardv2"
        f"?DayOffset=0&GameDate={game_date}&LeagueID=00"
    )

    try:

        r = requests.get(
            scoreboard_url,
            headers=HEADERS,
            timeout=30
        )

        if r.status_code != 200:
            print("FAILED:", r.status_code)
            current += timedelta(days=1)
            continue

        data = r.json()

    except Exception as e:
        print("ERROR:", e)
        current += timedelta(days=1)
        continue

    result_sets = data.get("resultSets", [])

    if not result_sets:
        current += timedelta(days=1)
        continue

    rows = result_sets[0].get("rowSet", [])

    print(f"GAMES FOUND: {len(rows)}")

    for row in rows:

        try:

            game_id = str(row[2])

            game_file = f"{game_id}.json"

            home_team = row[7]
            away_team = row[6]

            game_summary = {
                "game_id": game_id,
                "game_file": game_file,
                "home_team": home_team,
                "away_team": away_team,
                "date": current.strftime("%Y-%m-%d")
            }

            games.append(game_summary)

            boxscore_url = (
                "https://cdn.nba.com/static/json/liveData/boxscore/"
                f"boxscore_{game_id}.json"
            )

            print(f"DOWNLOADING {game_file}")

            br = requests.get(
                boxscore_url,
                headers=HEADERS,
                timeout=30
            )

            if br.status_code == 200:

                out_path = os.path.join(BOX_DIR, game_file)

                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(br.json(), f, indent=2)

            else:
                print("BOX FAILED:", br.status_code)

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

if len(final_games) < 1000:
    raise SystemExit("ABORTED - TOO FEW GAMES")

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(final_games, f, indent=2)

print("\nDONE")
print("TOTAL GAMES:", len(final_games))
