import requests
import json
from pathlib import Path

print("NHL SCORERS INCREMENTAL BUILDER")

SEASON = 2026  # change per run

SEASON_FILE = Path(f"docs/data/nhl/seasons/{SEASON}.json")
BOX_DIR = Path(f"docs/data/nhl/boxscores/{SEASON}")
BOX_DIR.mkdir(parents=True, exist_ok=True)

def fetch(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except:
        return {}
    return {}

if not SEASON_FILE.exists():
    print("Season file missing")
    exit()

games = json.loads(SEASON_FILE.read_text())

count = 0
MAX_PER_RUN = 200   # 🔥 prevents timeout

for game in games:

    game_id = game["game_id"]
    file_path = BOX_DIR / f"{game_id}.json"

    # ✅ skip existing
    if file_path.exists():
        continue

    print(f"Building {game_id}")

    pbp = fetch(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play")
    box = fetch(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore")

    try:
        plays = pbp.get("plays") or pbp.get("gameData", {}).get("plays") or []

        goals = []

        for play in plays:
            if play.get("typeDescKey") != "goal":
                continue

            d = play.get("details", {})

            goals.append({
                "period": play.get("periodDescriptor", {}).get("number"),
                "time": play.get("timeInPeriod"),
                "scorer": d.get("scoringPlayerName"),
                "assists": [
                    a for a in [
                        d.get("assist1PlayerName"),
                        d.get("assist2PlayerName")
                    ] if a
                ],
                "strength": d.get("strength")
            })

        game_json = {
            "game_id": game_id,
            "date": game["date"],
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "home_score": game["home_score"],
            "away_score": game["away_score"],
            "goals": goals
        }

        file_path.write_text(json.dumps(game_json, indent=2))

        count += 1

        if count >= MAX_PER_RUN:
            print("Hit run limit, stopping safely")
            break

    except Exception as e:
        print(f"FAILED {game_id}: {e}")
        continue

print("DONE")
