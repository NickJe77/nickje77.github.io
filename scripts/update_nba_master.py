#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path("docs/data/nba/2025")
BASE_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = datetime(2025, 2, 15)
END_DATE = datetime.today()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nba.com/",
    "Accept": "application/json"
}

def fetch_scoreboard(date):
    date_str = date.strftime("%Y%m%d")
    url = f"https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_{date_str}.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"{date_str} - blocked ({r.status_code})")
            return None
    except Exception as e:
        print(f"{date_str} - error: {e}")
        return None

def save_game(game):
    game_id = game["gameId"]
    file_path = BASE_DIR / f"{game_id}.json"
    if file_path.exists():
        return False
    with open(file_path, "w") as f:
        json.dump(game, f, indent=2)
    return True

def main():
    current_date = START_DATE
    new_games = 0

    while current_date <= END_DATE:
        data = fetch_scoreboard(current_date)
        if data and "scoreboard" in data:
            games = data["scoreboard"].get("games", [])
            for game in games:
                if game.get("gameStatusText") == "Final":
                    if save_game(game):
                        new_games += 1
        current_date += timedelta(days=1)

    print(f"Done. New games written: {new_games}")

if __name__ == "__main__":
    main()
