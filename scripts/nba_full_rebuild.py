import os
import json
import time
import random
import requests

SEASON = "2026"

BASE_DIR = os.getcwd()

SEASON_DIR = os.path.join(
    BASE_DIR,
    "docs",
    "data",
    "nba",
    SEASON
)

BOX_DIR = os.path.join(
    BASE_DIR,
    "docs",
    "data",
    "nba",
    "boxscores",
    SEASON
)

os.makedirs(SEASON_DIR, exist_ok=True)
os.makedirs(BOX_DIR, exist_ok=True)

INDEX_FILE = os.path.join(SEASON_DIR, "index.json")

HEADERS = {
    "Host": "stats.nba.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0 Safari/537.36"
    ),
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept-Language": "en-US,en;q=0.9"
}

session = requests.Session()

def fetch_game(game_id):

    url = (
        "https://stats.nba.com/stats/boxscoretraditionalv2"
        f"?GameID={game_id}"
        "&StartPeriod=0"
        "&EndPeriod=10"
        "&StartRange=0"
        "&EndRange=28800"
        "&RangeType=0"
    )

    for attempt in range(5):

        try:

            r = session.get(
                url,
                headers=HEADERS,
                timeout=30
            )

            if r.status_code == 200:
                return r.json()

            print(f"{game_id} STATUS {r.status_code}")

            if r.status_code == 403:

                wait = 20 + (attempt * 20)

                print(f"403 WAIT {wait}s")

                time.sleep(wait)

        except Exception as e:

            print(f"{game_id} ERROR", e)

        time.sleep(random.uniform(3, 6))

    return None

games = []

START_ID = 1
END_ID = 1500

for num in range(START_ID, END_ID + 1):

    game_id = f"00225{num:05d}"

    filename = f"{game_id}.json"

    out_path = os.path.join(BOX_DIR, filename)

    if os.path.exists(out_path):

        print("SKIP", filename)

        continue

    print("FETCH", filename)

    data = fetch_game(game_id)

    if not data:
        continue

    try:

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    except Exception as e:

        print("WRITE FAIL", e)

        continue

    games.append({
        "game_id": game_id,
        "game_file": filename
    })

    time.sleep(random.uniform(4, 8))

# REBUILD INDEX FROM FILES
index_games = []

files = sorted(
    f for f in os.listdir(BOX_DIR)
    if f.endswith(".json")
)

for filename in files:

    game_id = filename.replace(".json", "")

    index_games.append({
        "game_id": game_id,
        "game_file": filename
    })

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index_games, f, indent=2)

print("TOTAL FILES:", len(index_games))
print("DONE")
