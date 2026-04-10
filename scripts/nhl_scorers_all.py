import requests
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

print("NHL SCORERS (FINAL WORKING VERSION)")

BASE = Path("docs/data/nhl")
SEASONS = list(range(1967, 2026))

MAX_PER_RUN = 8000
count = 0

def fetch_json(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

def process_game(SEASON, game):
    game_id = game.get("game_id") or game.get("id")
    if not game_id:
        return None

    box_dir = BASE / f"boxscores/{SEASON}"
    file_path = box_dir / f"{game_id}.json"

    if file_path.exists():
        return None

    game_json = {
        "game_id": game_id,
        "date": game.get("date"),
        "home_team": game.get("home_team"),
        "away_team": game.get("away_team"),
        "home_score": game.get("home_score"),
        "away_score": game.get("away_score"),
        "goals": []
    }

    # ONLY MODERN ERA
    if SEASON >= 2005:

        pbp = fetch_json(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play")

        try:
            plays = pbp.get("plays", [])

            for play in plays:
                if play.get("typeDescKey") != "goal":
                    continue

                details = play.get("details", {})

                game_json["goals"].append({
                    "period": play.get("periodDescriptor", {}).get("number"),
                    "time": play.get("timeInPeriod"),
                    "scorer": details.get("scoringPlayerName"),
                    "assists": [
                        details.get("assist1PlayerName"),
                        details.get("assist2PlayerName")
                    ],
                    "strength": details.get("strength")
                })

        except Exception as e:
            print(f"⚠️ Failed parsing {game_id}")

    return (file_path, game_json)


tasks = []

for SEASON in SEASONS:
    season_file = BASE / f"seasons/{SEASON}.json"
    box_dir = BASE / f"boxscores/{SEASON}"
    box_dir.mkdir(parents=True, exist_ok=True)

    if not season_file.exists():
        continue

    games = json.loads(season_file.read_text())

    for game in games:
        game_id = game.get("game_id") or game.get("id")
        if not game_id:
            continue

        file_path = box_dir / f"{game_id}.json"

        if not file_path.exists():
            tasks.append((SEASON, game))

print(f"Queued games: {len(tasks)}")

with ThreadPoolExecutor(max_workers=12) as executor:
    futures = [executor.submit(process_game, s, g) for s, g in tasks]

    for future in as_completed(futures):
        result = future.result()

        if result:
            file_path, game_json = result
            file_path.write_text(json.dumps(game_json, indent=2))

            count += 1

            if count % 200 == 0:
                print(f"Built {count}")

            if count >= MAX_PER_RUN:
                print("🛑 Hit limit")
                break

print(f"DONE — built {count}")
