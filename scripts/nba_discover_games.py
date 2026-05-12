import os
import json
import requests
from datetime import datetime

OUTPUT_DIR = "docs/data/nba/2026"
INDEX_FILE = f"{OUTPUT_DIR}/index.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("NBA discover games starting")

URL = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com"
}

try:

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    print("Status:", response.status_code)

    response.raise_for_status()

    data = response.json()

except Exception as e:

    print("Failed to download NBA schedule")
    print("ERROR:", str(e))
    raise SystemExit(1)

games = data.get("scoreboard", {}).get("games", [])

print(f"Games found: {len(games)}")

out_games = []

for game in games:

    game_id = str(game.get("gameId", "")).strip()

    if not game_id:
        continue

    home_team = (
        game.get("homeTeam", {})
        .get("teamName", "")
    )

    away_team = (
        game.get("awayTeam", {})
        .get("teamName", "")
    )

    game_data = {
        "game_id": game_id,
        "home_team": home_team,
        "away_team": away_team,
        "game_file": f"{game_id}.json"
    }

    out_games.append(game_data)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(out_games, f, indent=2)

print(f"Saved {len(out_games)} games")
print("Done")
