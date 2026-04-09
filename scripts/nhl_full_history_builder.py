import requests
import json
from pathlib import Path
from datetime import datetime, timedelta

print("NHL FULL HISTORY BUILDER (1967 → NOW)")

BASE = Path("docs/data/nhl/seasons")
BASE.mkdir(parents=True, exist_ok=True)

START_YEAR = 1967
END_YEAR = 2026

def fetch_schedule(date):
    url = f"https://api-web.nhle.com/v1/schedule/{date}"
    try:
        return requests.get(url).json()
    except:
        return {}

def fetch_boxscore(game_id):
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
    try:
        return requests.get(url).json()
    except:
        return {}

for year in range(START_YEAR, END_YEAR + 1):

    print(f"\n=== SEASON {year} ===")

    # NHL season runs Oct → June
    start = datetime(year, 10, 1)
    end   = datetime(year + 1, 6, 30)

    games = []
    seen_ids = set()

    current = start

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        print(f"Checking {date_str}")

        data = fetch_schedule(date_str)

        for week in data.get("gameWeek", []):
            for game in week.get("games", []):

                game_id = game.get("id")
                game_type = game.get("gameType")

                # 2 = regular, 3 = playoffs
                if game_type not in [2, 3]:
                    continue

                if game_id in seen_ids:
                    continue

                seen_ids.add(game_id)

                # 🔥 GET REAL SCORE FROM BOXSCORE
                box = fetch_boxscore(game_id)

                try:
                    home = box.get("homeTeam", {})
                    away = box.get("awayTeam", {})

                    games.append({
                        "game_id": game_id,
                        "date": game.get("gameDate"),
                        "home_team": home.get("abbrev"),
                        "away_team": away.get("abbrev"),
                        "home_score": home.get("score"),
                        "away_score": away.get("score"),
                        "venue": box.get("venue", {}).get("default")
                    })
                except:
                    continue

        current += timedelta(days=1)

    print(f"Total games for {year}: {len(games)}")

    # SAVE PER SEASON
    out_file = BASE / f"{year}.json"
    out_file.write_text(json.dumps(games, indent=2))

    print(f"Saved {year}.json")

print("\nDONE")
