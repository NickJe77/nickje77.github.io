import requests
import json
import os
from datetime import datetime

BASE_DIR = "docs/data/nba"
SCHEDULE_URL = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"

os.makedirs(BASE_DIR, exist_ok=True)

print("NBA discover games starting")

r = requests.get(SCHEDULE_URL, timeout=30)
if r.status_code != 200:
    print("Failed to download NBA schedule")
    raise SystemExit(1)

data = r.json()
game_dates = data.get("leagueSchedule", {}).get("gameDates", [])

season_games = {}

for d in game_dates:
    for g in d.get("games", []):
        game_id = str(g.get("gameId", "")).strip()
        game_date = g.get("gameDateEst", "").strip()

        if not game_id or not game_date:
            continue

        # skip preseason
        if game_id.startswith("001"):
            continue

        try:
            dt = datetime.fromisoformat(game_date.replace("Z", ""))
        except Exception:
            continue

        # NBA season folder = season start year
        if dt.month >= 10:
            season = dt.year
        else:
            season = dt.year - 1

        season_games.setdefault(season, set()).add(game_id)

for season, games in season_games.items():
    season_dir = os.path.join(BASE_DIR, str(season))
    os.makedirs(season_dir, exist_ok=True)

    index_path = os.path.join(season_dir, "index.json")
    index = {
        "season": season,
        "games": sorted(games)
    }

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print(f"Updated {index_path} with {len(index['games'])} games")

print("NBA discover games finished")
