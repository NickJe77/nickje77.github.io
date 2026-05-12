import os
import json
import time
import random
import requests
from datetime import datetime, timedelta

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

games = []

def get_json(url):

    try:

        r = session.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if r.status_code == 200:
            return r.json()

        print("STATUS:", r.status_code)

    except Exception as e:

        print("REQUEST ERROR:", e)

    return None

# BUILD REAL GAME IDS FROM SCHEDULE
start_date = datetime(2025, 10, 1)
end_date = datetime.now()

found_ids = set()

current = start_date

while current <= end_date:

    date_str = current.strftime("%m/%d/%Y")

    print(f"\nSCHEDULE {date_str}")

    url = (
        "https://stats.nba.com/stats/scoreboardv2"
        f"?DayOffset=0&GameDate={date_str}&LeagueID=00"
    )

    data = get_json(url)

    if not data:
        current += timedelta(days=1)
        time.sleep(5)
        continue

    result_sets = data.get("resultSets", [])

    if not result_sets:
        current += timedelta(days=1)
        continue

    rows = result_sets[0].get("rowSet", [])

    for row in rows:

        try:

            game_id = str(row[2])

            if game_id:
                found_ids.add(game_id)

        except Exception:
            pass

    print("TOTAL IDS:", len(found_ids))

    current += timedelta(days=1)

    time.sleep(random.uniform(2, 5))

print("\nREAL GAMES FOUND:", len(found_ids))

# DOWNLOAD ONLY REAL GAMES
for game_id in sorted(found_ids):

    filename = f"{game_id}.json"

    out_path = os.path.join(BOX_DIR, filename)

    if os.path.exists(out_path):

        print("SKIP", filename)

        continue

    print("FETCH", filename)

    url = (
        "https://cdn.nba.com/static/json/liveData/boxscore/"
        f"boxscore_{game_id}.json"
    )

    data = get_json(url)

    if not data:
        continue

    game = data.get("game", {})

    if not game:
        continue

    try:

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    except Exception as e:

        print("WRITE FAIL", e)

        continue

    home_team = (
        game.get("homeTeam", {})
        .get("teamName", "")
    )

    away_team = (
        game.get("awayTeam", {})
        .get("teamName", "")
    )

    game_date = (
        game.get("gameEt")
        or game.get("gameTimeUTC")
        or ""
    )

    games.append({
        "game_id": game_id,
        "game_file": filename,
        "home_team": home_team,
        "away_team": away_team,
        "date": game_date
    })

    print("SAVED", filename)

    time.sleep(random.uniform(2, 4))

games.sort(
    key=lambda x: (x.get("date", ""), x.get("game_id", ""))
)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(games, f, indent=2)

print("\nDONE")
print("TOTAL GAMES:", len(games))
