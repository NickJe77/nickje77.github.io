import requests
import json
import time
from pathlib import Path
from datetime import datetime

print("MLB 2026 FULL GAME BUILDER (FIXED)")

BASE = "https://statsapi.mlb.com/api"
SEASON = 2026

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

OUT_DIR = Path(f"docs/data/baseball/games/{SEASON}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
# SAFE TEAM NAME
# -------------------------
def get_team_code(team):
    return (
        team.get("abbreviation")
        or team.get("teamName")
        or team.get("name")
        or "UNK"
    )

# -------------------------
# GET SCHEDULE
# -------------------------
def get_schedule():
    url = f"{BASE}/v1/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url).json()

    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):

            if g.get("gameType") not in ["R", "P"]:
                continue

            home_team = g.get("teams", {}).get("home", {}).get("team", {})
            away_team = g.get("teams", {}).get("away", {}).get("team", {})

            games.append({
                "id": g.get("gamePk"),
                "date": g.get("officialDate"),
                "home": get_team_code(home_team),
                "away": get_team_code(away_team)
            })

    return games

# -------------------------
# GET GAME FEED
# -------------------------
def get_game(game_id):
    url = f"{BASE}/v1.1/game/{game_id}/feed/live"
    r = requests.get(url)

    if r.status_code != 200:
        print("FAILED", game_id)
        return None

    return r.json()

# -------------------------
# BUILD EVENTS
# -------------------------
def build_events(data):
    plays = data.get("liveData", {}).get("plays", {}).get("allPlays", [])
    events = []

    for p in plays:
        events.append([
            "play",
            str(p.get("about", {}).get("inning")),
            str(p.get("about", {}).get("halfInning")),
            str(p.get("matchup", {}).get("batter", {}).get("id")),
            str(p.get("count", {}).get("outs")),
            p.get("result", {}).get("event"),
            p.get("result", {}).get("description")
        ])

    return events

# -------------------------
# MAIN
# -------------------------
games = get_schedule()

print("TOTAL GAMES:", len(games))

for g in games:

    game_id = str(g["id"])
    file_path = OUT_DIR / f"{game_id}.json"

    if file_path.exists():
        continue

    data = get_game(game_id)

    if not data:
        continue

    output = {
        "game_id": game_id,
        "date": g["date"],
        "season": SEASON,
        "home_code": g["home"],
        "away_code": g["away"],
        "home_team": g["home"],
        "away_team": g["away"],
        "events": build_events(data)
    }

    file_path.write_text(json.dumps(output, indent=2))

    print("✔ Saved", game_id)

    time.sleep(0.4)

print("DONE")
