import requests
import json
from pathlib import Path
import time
import re

print("MLB PLAY-BY-PLAY BUILDER (2025 FORMAT MATCH)")

# -------------------------
# CONFIG
# -------------------------
SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

SEASON_FILE = Path(f"docs/data/baseball/seasons/{SEASON}.json")
OUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")

OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -------------------------
# LOAD SEASON DATA
# -------------------------
if not SEASON_FILE.exists():
    print("❌ Missing season file")
    exit()

with open(SEASON_FILE) as f:
    season_data = json.load(f)

games = season_data.get("games", [])

print(f"Loaded {len(games)} games")


# -------------------------
# TEAM CODE MAP (expandable)
# -------------------------
TEAM_CODES = {
    "Toronto Blue Jays": "TOR",
    "Athletics": "OAK",
    "Los Angeles Dodgers": "LAN",
    "Chicago Cubs": "CHN",
}


# -------------------------
# BUILD BATTER ID (RETRO STYLE)
# -------------------------
def build_player_id(name):
    if not name:
        return ""

    parts = name.lower().split()

    if len(parts) == 1:
        return parts[0][:8]

    last = parts[-1][:5]
    first = parts[0][:3]

    return f"{last}{first}01"


# -------------------------
# SIMPLE RESULT CODE MAPPER
# -------------------------
def map_result(desc):
    d = desc.lower()

    if "strikeout" in d:
        return "K"
    if "walk" in d:
        return "BB"
    if "hit by pitch" in d:
        return "HBP"
    if "home run" in d:
        return "HR"
    if "double" in d:
        return "2B"
    if "triple" in d:
        return "3B"
    if "single" in d:
        return "1B"
    if "grounded out" in d:
        return "GO"
    if "fly out" in d:
        return "FO"

    return "X"


# -------------------------
# FETCH PLAY BY PLAY
# -------------------------
def fetch_pbp(game_id):
    url = f"{BASE}/game/{game_id}/playByPlay"

    try:
        r = requests.get(url, headers=HEADERS)
        return r.json()
    except:
        return None


# -------------------------
# BUILD EVENTS (MATCH 2025 SHAPE)
# -------------------------
def build_events(data):
    events = []

    for play in data.get("allPlays", []):

        about = play.get("about", {})
        result = play.get("result", {})
        matchup = play.get("matchup", {})

        inning = str(about.get("inning"))

        # 0 = top, 1 = bottom (your format)
        half = "0" if about.get("halfInning") == "top" else "1"

        batter_name = matchup.get("batter", {}).get("fullName", "")
        batter_id = build_player_id(batter_name)

        desc = result.get("description", "")

        # ⚠️ placeholders where MLB API doesn't give exact retro fields
        count = "00"
        pitch_seq = ""
        result_code = map_result(desc)

        events.append([
            "play",
            inning,
            half,
            batter_id,
            count,
            pitch_seq,
            result_code
        ])

    return events


# -------------------------
# MAIN
# -------------------------
saved = 0
failed = 0

for g in games:
    game_id = g["game_id"]
    status = g.get("status", "")

    if status != "Final":
        continue

    print(f"Processing {game_id}")

    pbp = fetch_pbp(game_id)

    if not pbp or "allPlays" not in pbp:
        print("❌ FAILED:", game_id)
        failed += 1
        continue

    home_team = g["home_team"]
    away_team = g["away_team"]

    home_code = TEAM_CODES.get(home_team, home_team[:3].upper())
    away_code = TEAM_CODES.get(away_team, away_team[:3].upper())

    game = {
        "game_id": game_id,
        "date": g["date"][:10],
        "season": SEASON,
        "home_code": home_code,
        "away_code": away_code,
        "home_team": home_code,
        "away_team": away_code,
        "events": build_events(pbp)
    }

    with open(OUT_DIR / f"{game_id}.json", "w") as f:
        json.dump(game, f, indent=2)

    saved += 1
    time.sleep(0.4)


# -------------------------
# SUMMARY
# -------------------------
print("\nDONE")
print(f"Saved: {saved}")
print(f"Failed: {failed}")
