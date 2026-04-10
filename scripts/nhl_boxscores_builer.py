import requests
import json
from pathlib import Path
from datetime import datetime, timedelta

print("NHL BOXSCORE BUILDER (WITH GOALS)")

SEASON = 2026

BASE = Path("docs/data/nhl")
BOX_DIR = BASE / f"boxscores/{SEASON}"
BOX_DIR.mkdir(parents=True, exist_ok=True)

START = datetime(2025, 10, 1)
END   = datetime(2026, 6, 30)

def fetch_schedule(date):
    url = f"https://api-web.nhle.com/v1/schedule/{date}"
    try:
        return requests.get(url).json()
    except:
        return {}

def fetch_boxscore(game_id):
    try:
        return requests.get(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore").json()
    except:
        return {}

def fetch_pbp(game_id):
    try:
        return requests.get(f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play").json()
    except:
        return {}

current = START

while current <= END:

    date_str = current.strftime("%Y-%m-%d")
    print(f"Checking {date_str}")

    data = fetch_schedule(date_str)

    for week in data.get("gameWeek", []):
        for game in week.get("games", []):

            game_id = game.get("id")
            game_type = game.get("gameType")

            if game_type not in [2, 3]:
                continue

            file_path = BOX_DIR / f"{game_id}.json"

            # ✅ DO NOT OVERWRITE EXISTING
            if file_path.exists():
                continue

            print(f"Building game {game_id}")

            box = fetch_boxscore(game_id)
            pbp = fetch_pbp(game_id)

            try:
                home = box.get("homeTeam", {})
                away = box.get("awayTeam", {})

                goals = []

                for play in pbp.get("plays", []):

                    # Goal event
                    if play.get("typeDescKey") != "goal":
                        continue

                    details = play.get("details", {})

                    scorer = details.get("scoringPlayerName")
                    assists = details.get("assist1PlayerName"), details.get("assist2PlayerName")

                    goals.append({
                        "period": play.get("periodDescriptor", {}).get("number"),
                        "time": play.get("timeInPeriod"),
                        "team": details.get("eventOwnerTeamId"),
                        "scorer": scorer,
                        "assists": [a for a in assists if a],
                        "strength": details.get("strength")
                    })

                game_json = {
                    "game_id": game_id,
                    "date": game.get("gameDate"),
                    "home_team": home.get("abbrev"),
                    "away_team": away.get("abbrev"),
                    "home_score": home.get("score"),
                    "away_score": away.get("score"),
                    "venue": box.get("venue", {}).get("default"),
                    "goals": goals
                }

                file_path.write_text(json.dumps(game_json, indent=2))

            except:
                continue

    current += timedelta(days=1)

print("DONE")
