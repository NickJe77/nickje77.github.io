import requests
import json
from pathlib import Path
from datetime import datetime, timedelta

print("NHL 2026 BUILDER")

OUTPUT = Path("docs/data/nhl/seasons/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

START = datetime(2025, 10, 1)   # season start approx
END   = datetime(2026, 6, 30)   # playoffs end approx

games = []

def fetch_day(date):
    url = f"https://api-web.nhle.com/v1/schedule/{date.strftime('%Y-%m-%d')}"
    try:
        res = requests.get(url)
        data = res.json()
        return data.get("gameWeek", [])
    except:
        return []

current = START

while current <= END:
    print(f"Checking {current.date()}")

    weeks = fetch_day(current)

    for week in weeks:
        for game in week.get("games", []):

            game_type = game.get("gameType")

            # 2 = regular season, 3 = playoffs
            if game_type not in [2, 3]:
                continue

            try:
                games.append({
                    "game_id": game.get("id"),
                    "date": game.get("gameDate"),
                    "home_team": game.get("homeTeam", {}).get("abbrev"),
                    "away_team": game.get("awayTeam", {}).get("abbrev"),
                    "home_score": game.get("homeTeam", {}).get("score"),
                    "away_score": game.get("awayTeam", {}).get("score"),
                    "venue": game.get("venue", {}).get("default")
                })
            except:
                continue

    current += timedelta(days=1)

print(f"Total games: {len(games)}")

# SAVE
OUTPUT.write_text(json.dumps(games, indent=2))
print("Saved 2026.json")nhl
