import requests
import json
from pathlib import Path
from datetime import datetime
import time

print("MLB 2026 REBUILD (EVENT STRUCTURE)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1.1"

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
BOX_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -------------------------------------------------
# GET SCHEDULE
# -------------------------------------------------
def get_schedule():
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            gamePk = str(g["gamePk"])
            gameDate = g["gameDate"][:10]

            home = g["teams"]["home"]["team"]["abbreviation"]
            away = g["teams"]["away"]["team"]["abbreviation"]

            games.append({
                "game_id": gamePk,
                "date": gameDate,
                "home": home,
                "away": away
            })

    print(f"Found {len(games)} games")
    return games


# -------------------------------------------------
# BUILD EVENTS FROM PLAY-BY-PLAY
# -------------------------------------------------
def get_game(game):
    game_id = game["game_id"]

    url = f"{BASE}/game/{game_id}/feed/live"

    try:
        data = requests.get(url, headers=HEADERS, timeout=20).json()
    except:
        print(f"Failed {game_id}")
        return None

    try:
        plays = data["liveData"]["plays"]["allPlays"]

        events = []

        for p in plays:
            about = p.get("about", {})
            matchup = p.get("matchup", {})
            result = p.get("result", {})

            inning = str(about.get("inning", ""))
            is_top = about.get("isTopInning", True)
            half = "1" if is_top else "0"

            batter = matchup.get("batter", {}).get("id", "")
            count = f"{p.get('count', {}).get('balls', 0)}{p.get('count', {}).get('strikes', 0)}"

            event = result.get("event", "")

            events.append([
                "play",
                inning,
                half,
                str(batter),
                count,
                event
            ])

        file_name = f"{game['date']}_{game['away']}_{game['home']}.json"

        game_json = {
            "game_id": game_id,
            "date": game["date"],
            "season": SEASON,
            "home_code": game["home"],
            "away_code": game["away"],
            "home_team": game["home"],
            "away_team": game["away"],
            "events": events
        }

        with open(BOX_DIR / file_name, "w") as f:
            json.dump(game_json, f, indent=2)

        print(f"Saved {file_name}")
        return True

    except Exception as e:
        print(f"Error {game_id}: {e}")
        return None


# -------------------------------------------------
# MAIN
# -------------------------------------------------
games = get_schedule()

count = 0

for g in games:
    ok = get_game(g)

    if ok:
        count += 1

    time.sleep(0.3)

print(f"DONE: {count} games built")
