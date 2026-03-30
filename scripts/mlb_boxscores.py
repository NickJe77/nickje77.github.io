import requests
import json
from pathlib import Path
import time

print("MLB PLAY-BY-PLAY BUILDER (MATCHES 2025)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

SEASON_FILE = Path(f"docs/data/baseball/seasons/{SEASON}.json")
OUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")

OUT_DIR.mkdir(parents=True, exist_ok=True)

data = json.load(open(SEASON_FILE))
games = data["games"]


# -------------------------
# TEAM CODE MAP (CRITICAL)
# -------------------------
TEAM_CODES = {
    "Chicago Cubs": "CHN",
    "Los Angeles Dodgers": "LAN",
    "Toronto Blue Jays": "TOR",
    "Athletics": "OAK",
    # ⚠️ we can expand this fully after test
}


# -------------------------
# GET PLAY BY PLAY
# -------------------------
def get_pbp(game_id):
    url = f"{BASE}/game/{game_id}/playByPlay"

    try:
        return requests.get(url).json()
    except:
        return None


# -------------------------
# BUILD EVENTS
# -------------------------
def build_events(data):
    events = []

    for play in data.get("allPlays", []):
        about = play.get("about", {})
        result = play.get("result", {})
        matchup = play.get("matchup", {})

        inning = about.get("inning")
        half = about.get("halfInning")
        desc = result.get("description")

        batter = matchup.get("batter", {}).get("fullName")

        events.append([
            "play",
            str(inning),
            half,
            batter,
            desc
        ])

    return events


# -------------------------
# MAIN
# -------------------------
for g in games:
    gid = g["game_id"]

    if g["status"] != "Final":
        continue

    print("Processing", gid)

    pbp = get_pbp(gid)

    if not pbp or "allPlays" not in pbp:
        print("FAILED", gid)
        continue

    home_team = g["home_team"]
    away_team = g["away_team"]

    home_code = TEAM_CODES.get(home_team, home_team[:3].upper())
    away_code = TEAM_CODES.get(away_team, away_team[:3].upper())

    game = {
        "game_id": gid,
        "date": g["date"][:10],
        "season": SEASON,
        "home_code": home_code,
        "away_code": away_code,
        "home_team": home_code,
        "away_team": away_code,
        "events": build_events(pbp)
    }

    with open(OUT_DIR / f"{gid}.json", "w") as f:
        json.dump(game, f, indent=2)

    time.sleep(0.4)
