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
    "Host": "stats.nba.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0 Safari/537.36"
    ),
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Accept-Language": "en-US,en;q=0.9"
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
            print("SCOREBOARD FAILED:", r.status_code)
            current += timedelta(days=1)
            continue

        data = r.json()

    except Exception as e:
        print("SCOREBOARD ERROR:", e)
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
                "https://stats.nba.com/stats/boxscoretraditionalv2"
                f"?GameID={game_id}"
                "&StartPeriod=0"
                "&EndPeriod=10"
                "&StartRange=0"
                "&EndRange=28800"
                "&RangeType=0"
            )

            print(f"DOWNLOADING {game_file}")

            try:

                br = requests.get(
                    boxscore_url,
                    headers=HEADERS,
                    timeout=30
                )

                if br.status_code != 200:
                    print("BOX FAILED:", br.status_code)
                    continue

                box_data = br.json()

                out_path = os.path.join(BOX_DIR, game_file)

                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(box_data, f, indent=2)

                print(f"SAVED {game_file}")

            except Exception as e:
                print("BOX ERROR:", e)

            time.sleep(0.6)

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
