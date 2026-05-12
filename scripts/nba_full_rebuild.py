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

            if r.status_code == 403:

                wait = 30 + (attempt * 30)

                print(f"403 BLOCKED - WAITING {wait}s")

                time.sleep(wait)

        except Exception as e:

            print("REQUEST ERROR:", e)

            wait = 15 + (attempt * 15)

            print(f"WAITING {wait}s")

            time.sleep(wait)

    return None

# RESUME FROM WHERE IT STARTED BLOCKING
START_ID = 1231

# SAFE BUFFER ABOVE CURRENT NBA GAME COUNTS
END_ID = 1500

for num in range(START_ID, END_ID + 1):

    game_id = f"00225{num:05d}"

    game_file = f"{game_id}.json"

    existing_path = os.path.join(BOX_DIR, game_file)

    # SKIP EXISTING FILES
    if os.path.exists(existing_path):

        print(f"SKIPPING EXISTING {game_file}")

        try:

            with open(existing_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            game = data.get("game", {})

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

        except Exception:
            pass

        continue

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

    try:

        with open(existing_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print("SAVED:", existing_path)

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

    # SLOWER REQUEST RATE TO AVOID 403 BLOCKS
    time.sleep(1.5)

# REBUILD INDEX FROM ALL FILES ON DISK
all_games = []

files = sorted(
    f for f in os.listdir(BOX_DIR)
    if f.endswith(".json")
)

print("TOTAL FILES FOUND:", len(files))

for filename in files:

    path = os.path.join(BOX_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception:
        continue

    game = data.get("game", {})

    if not game:
        continue

    game_id = filename.replace(".json", "")

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

    all_games.append({
        "game_id": game_id,
        "game_file": filename,
        "home_team": home_team,
        "away_team": away_team,
        "date": game_date
    })

all_games.sort(
    key=lambda x: (x.get("date", ""), x.get("game_id", ""))
)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(all_games, f, indent=2)

print("INDEX WRITTEN:", INDEX_FILE)
print("TOTAL GAMES:", len(all_games))
print("DONE")
