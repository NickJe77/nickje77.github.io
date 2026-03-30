import requests
import json
from pathlib import Path
import time

print("MLB PLAY-BY-PLAY BUILDER (ADVANCED MATCH)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

SEASON_FILE = Path(f"docs/data/baseball/seasons/{SEASON}.json")
OUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")

OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

with open(SEASON_FILE) as f:
    season_data = json.load(f)

games = season_data["games"]


# -------------------------
# PLAYER ID
# -------------------------
def player_id(name):
    if not name:
        return ""
    parts = name.lower().split()
    if len(parts) == 1:
        return parts[0][:8]
    return f"{parts[-1][:5]}{parts[0][:3]}01"


# -------------------------
# PITCH CODE BUILDER
# -------------------------
def build_pitch_seq(events):
    seq = ""

    for e in events:
        details = e.get("details", {})
        code = details.get("code", "")

        if code:
            seq += code

    return seq


# -------------------------
# COUNT BUILDER
# -------------------------
def build_count(play):
    count = play.get("count", {})
    balls = count.get("balls", 0)
    strikes = count.get("strikes", 0)
    return f"{balls}{strikes}"


# -------------------------
# RESULT CODE
# -------------------------
def result_code(play):
    desc = play.get("result", {}).get("description", "").lower()

    if "strikeout" in desc:
        return "K"
    if "walk" in desc:
        return "BB"
    if "home run" in desc:
        return "HR"
    if "double" in desc:
        return "2B"
    if "single" in desc:
        return "1B"
    if "grounded out" in desc:
        return "GO"
    if "fly out" in desc:
        return "FO"

    return "X"


# -------------------------
# FETCH PBP
# -------------------------
def fetch(game_id):
    url = f"{BASE}/game/{game_id}/playByPlay"
    return requests.get(url, headers=HEADERS).json()


# -------------------------
# BUILD EVENTS
# -------------------------
def build_events(data):
    events = []

    for play in data.get("allPlays", []):

        about = play.get("about", {})
        matchup = play.get("matchup", {})

        inning = str(about.get("inning"))
        half = "0" if about.get("halfInning") == "top" else "1"

        batter = matchup.get("batter", {}).get("fullName", "")
        batter = player_id(batter)

        pitch_seq = build_pitch_seq(play.get("playEvents", []))
        count = build_count(play)
        res = result_code(play)

        events.append([
            "play",
            inning,
            half,
            batter,
            count,
            pitch_seq,
            res
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

    pbp = fetch(gid)

    if "allPlays" not in pbp:
        print("FAILED", gid)
        continue

    game = {
        "game_id": gid,
        "date": g["date"][:10],
        "season": SEASON,
        "home_code": g["home_team"][:3].upper(),
        "away_code": g["away_team"][:3].upper(),
        "home_team": g["home_team"][:3].upper(),
        "away_team": g["away_team"][:3].upper(),
        "events": build_events(pbp)
    }

    with open(OUT_DIR / f"{gid}.json", "w") as f:
        json.dump(game, f, indent=2)

    time.sleep(0.4)
