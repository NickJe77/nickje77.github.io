import requests
import json
import time
from datetime import datetime
from pathlib import Path

print("MLB UPDATER (FULL WITH EVENTS)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

# 🔥 KEEP YOUR EXISTING STRUCTURE
SEASON_DIR = Path("docs/data/baseball/seasons")
GAMES_DIR = Path(f"docs/data/baseball/games/{SEASON}")

SEASON_DIR.mkdir(parents=True, exist_ok=True)
GAMES_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------
# GET SCHEDULE (ONLY REGULAR + POSTSEASON)
# -------------------------------------------------
def get_schedule():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            # ONLY REGULAR + POSTSEASON
            if g.get("gameType") not in ["R", "P"]:
                continue

            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["gameDate"][:10],
                "home": g["teams"]["home"]["team"]["name"],
                "away": g["teams"]["away"]["team"]["name"]
            })

    print(f"Found {len(games)} games")
    return games


# -------------------------------------------------
# EXTRACT EVENTS (PLAY-BY-PLAY)
# -------------------------------------------------
def extract_events(game_data):
    events = []

    plays = game_data.get("liveData", {}).get("plays", {}).get("allPlays", [])

    for play in plays:
        try:
            about = play.get("about", {})
            result = play.get("result", {})
            matchup = play.get("matchup", {})

            events.append({
                "inning": about.get("inning"),
                "half": about.get("halfInning"),
                "event": result.get("event"),
                "description": result.get("description"),
                "rbi": result.get("rbi"),
                "outs": about.get("outs"),
                "batter": matchup.get("batter", {}).get("fullName"),
                "pitcher": matchup.get("pitcher", {}).get("fullName")
            })

        except:
            continue

    return events


# -------------------------------------------------
# DOWNLOAD SINGLE GAME
# -------------------------------------------------
def download_game(game):
    game_id = game["game_id"]
    file_path = GAMES_DIR / f"{game_id}.json"

    # skip if already exists
    if file_path.exists():
        return

    url = f"{BASE}/game/{game_id}/feed/live"

    try:
        r = requests.get(url, headers=HEADERS)

        if r.status_code != 200:
            print(f"FAILED {game_id}")
            return

        data = r.json()

        teams = data.get("gameData", {}).get("teams", {})

        home = teams.get("home", {}).get("name", "")
        away = teams.get("away", {}).get("name", "")

        # 🔥 EVENTS FIX
        events = extract_events(data)

        game_json = {
            "game_id": game_id,
            "date": game["date"],
            "season": SEASON,
            "home_code": home,
            "away_code": away,
            "home_team": home,
            "away_team": away,
            "events": events
        }

        with open(file_path, "w") as f:
            json.dump(game_json, f, indent=2)

        print(f"{game_id} saved ({len(events)} events)")

        time.sleep(0.3)

    except Exception as e:
        print(f"ERROR {game_id}: {e}")


# -------------------------------------------------
# BUILD SEASON INDEX (OPTIONAL BUT USEFUL)
# -------------------------------------------------
def build_season_file(games):
    output = {
        "season": SEASON,
        "games": games
    }

    with open(SEASON_DIR / f"{SEASON}.json", "w") as f:
        json.dump(output, f, indent=2)


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    games = get_schedule()

    for g in games:
        download_game(g)

    build_season_file(games)

    print("DONE")


if __name__ == "__main__":
    main()
