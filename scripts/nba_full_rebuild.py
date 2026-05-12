import os
import json
import time
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

print("SEASON DIR:", SEASON_DIR)
print("BOX DIR:", BOX_DIR)

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

def fetch_json(url):

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

    return None

START_ID = 1
END_ID = 1500

for num in range(START_ID, END_ID + 1):

    game_id = f"00225{num:05d}"

    game_file = f"{game_id}.json"

    print(f"FETCHING {game_file}")

    url = (
        "https://cdn.nba.com/static/json/liveData/boxscore/"
        f"boxscore_{game_id}.json"
    )

    data = fetch_json(url)

    if not data:
        continue

    game = data.get("game", {})

    if not game:
        continue

    out_path = os.path.join(BOX_DIR, game_file)

    try:

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print("SAVED:", out_path)

    except Exception as e:
        print("WRITE ERROR:", e)
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
        "game_file": game_file,
        "home_team": home_team,
        "away_team": away_team,
        "date": game_date
    })

    time.sleep(0.2)

games.sort(
    key=lambda x: (x.get("date", ""), x.get("game_id", ""))
)

print("TOTAL GAMES:", len(games))

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(games, f, indent=2)

print("INDEX WRITTEN:", INDEX_FILE)

print("DONE")
