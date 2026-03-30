import requests
import json
from pathlib import Path
from datetime import datetime
import time

print("MLB DEBUG SCRAPER")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

SEASON_DIR = Path("docs/data/baseball/seasons")
BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")

SEASON_DIR.mkdir(parents=True, exist_ok=True)
BOX_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------
# GET SCHEDULE
# -----------------------------------
def get_schedule():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"

    print("REQUESTING:", url)

    r = requests.get(url, headers=HEADERS)

    print("STATUS CODE:", r.status_code)

    data = r.json()

    print("DATES FOUND:", len(data.get("dates", [])))

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            print("GAME FOUND:", g.get("gamePk"), g.get("gameType"))

            if g.get("gameType") not in ["R", "P"]:
                print("SKIPPED (not regular/postseason)")
                continue

            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["gameDate"],
                "home_team": g["teams"]["home"]["team"]["name"],
                "away_team": g["teams"]["away"]["team"]["name"],
            })

    print("TOTAL VALID GAMES:", len(games))

    return games


# -----------------------------------
# GET BOXSCORE
# -----------------------------------
def get_boxscore(game_id):
    url = f"{BASE}/game/{game_id}/boxscore"

    print("BOX REQUEST:", url)

    r = requests.get(url, headers=HEADERS)

    print("BOX STATUS:", r.status_code)

    try:
        data = r.json()
    except:
        print("FAILED JSON")
        return None

    if "teams" not in data:
        print("NO TEAMS IN RESPONSE")
        return None

    print("BOX OK:", game_id)

    return data


# -----------------------------------
# MAIN
# -----------------------------------
def run():
    games = get_schedule()

    if not games:
        print("❌ NO GAMES FOUND — THIS IS THE PROBLEM")
        return

    for g in games[:5]:  # only test first 5
        gid = g["game_id"]

        box = get_boxscore(gid)

        if not box:
            print("❌ FAILED:", gid)
            continue

        outfile = BOX_DIR / f"{gid}.json"

        with open(outfile, "w") as f:
            json.dump(box, f, indent=2)

        print("✅ SAVED:", gid)

        time.sleep(1)


if __name__ == "__main__":
    run()
