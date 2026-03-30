import requests
import json
import time
from pathlib import Path
from datetime import datetime

print("MLB 2026 BOXSCORE BUILDER (CORRECT FORMAT)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
BOX_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
# GET SCHEDULE
# -------------------------
def get_schedule():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            # ONLY REGULAR + PLAYOFFS
            if g.get("gameType") not in ["R", "P"]:
                continue

            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["officialDate"]
            })

    return games


# -------------------------
# GET BOXSCORE
# -------------------------
def get_boxscore(game_id):
    url = f"{BASE}/game/{game_id}/boxscore"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("FAILED", game_id)
        return None

    return r.json()


# -------------------------
# EXTRACT PLAYERS
# -------------------------
def extract_batting(team):
    players = []

    for p in team.get("players", {}).values():

        person = p.get("person", {})
        stats = p.get("stats", {}).get("batting", {})

        players.append({
            "player": person.get("fullName"),
            "hits": stats.get("hits", 0),
            "runs": stats.get("runs", 0),
            "rbi": stats.get("rbi", 0),
            "home_runs": stats.get("homeRuns", 0)
        })

    return players


def extract_pitching(team):
    players = []

    for p in team.get("players", {}).values():

        person = p.get("person", {})
        stats = p.get("stats", {}).get("pitching", {})

        if not stats:
            continue

        players.append({
            "player": person.get("fullName"),
            "ip": stats.get("inningsPitched"),
            "hits": stats.get("hits"),
            "runs": stats.get("runs"),
            "er": stats.get("earnedRuns"),
            "bb": stats.get("baseOnBalls"),
            "so": stats.get("strikeOuts")
        })

    return players


# -------------------------
# MAIN
# -------------------------
games = get_schedule()

print("TOTAL GAMES:", len(games))

for g in games:

    game_id = g["game_id"]
    file_path = BOX_DIR / f"{game_id}.json"

    # SKIP EXISTING
    if file_path.exists():
        continue

    data = get_boxscore(game_id)

    if not data:
        continue

    away_team = data["teams"]["away"]
    home_team = data["teams"]["home"]

    output = {
        "batters_away": extract_batting(away_team),
        "batters_home": extract_batting(home_team),
        "pitchers_away": extract_pitching(away_team),
        "pitchers_home": extract_pitching(home_team)
    }

    file_path.write_text(json.dumps(output, indent=2))

    print("✔ Saved", game_id)

    # polite delay
    time.sleep(0.4)

print("DONE")
