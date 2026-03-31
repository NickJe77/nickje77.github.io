import requests
import json
from pathlib import Path
import time

print("MLB PLAY-BY-PLAY BUILDER (FINAL)")

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
# TEAM CODE MAP
# -------------------------
TEAM_CODES = {
    "Toronto Blue Jays": "TOR",
    "Athletics": "ATH",
    "Los Angeles Dodgers": "LAN",
    "Chicago Cubs": "CHN",
}


# -------------------------
# PLAYER ID BUILDER
# -------------------------
def player_id(name):
    if not name:
        return ""

    parts = name.lower().split()

    if len(parts) == 1:
        return parts[0][:8]

    return f"{parts[-1][:5]}{parts[0][:3]}01"


# -------------------------
# BUILD PITCH SEQUENCE
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
# BUILD COUNT
# -------------------------
def build_count(play):
    count = play.get("count", {})
    balls = count.get("balls", 0)
    strikes = count.get("strikes", 0)
    return f"{balls}{strikes}"


# -------------------------
# RESULT CODE (IMPROVED)
# -------------------------
def result_code(play):
    result = play.get("result", {})
    desc = result.get("description", "").lower()
    event = result.get("eventType", "")

    # STRIKEOUT
    if event == "strikeout":
        return "K"

    # WALK
    if event == "walk":
        return "BB"

    # HITS
    if event == "single":
        return "1B"
    if event == "double":
        return "2B"
    if event == "triple":
        return "3B"
    if event == "home_run":
        return "HR"

    # OUT TYPES
    if "grounded out" in desc:
        return "GO"
    if "fly out" in desc:
        return "FO"
    if "lined out" in desc:
        return "LO"
    if "pop out" in desc:
        return "PO"

    # PLAYS
    if "double play" in desc:
        return "DP"
    if "force out" in desc:
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
# BUILD EVENTS
# -------------------------
def build_events(data):
    events = []

    for play in data.get("allPlays", []):

        about = play.get("about", {})
        matchup = play.get("matchup", {})

        inning = str(about.get("inning"))

        # 0 = top, 1 = bottom
        half = "0" if about.get("halfInning") == "top" else "1"

        batter_name = matchup.get("batter", {}).get("fullName", "")
        batter = player_id(batter_name)

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
saved = 0
failed = 0

for g in games:
    gid = g["game_id"]
    status = g.get("status", "")

    if status != "Final":
        continue

    print(f"Processing {gid}")

    pbp = fetch_pbp(gid)

    if not pbp or "allPlays" not in pbp:
        print("❌ FAILED:", gid)
        failed += 1
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

    saved += 1
    time.sleep(0.4)


# -------------------------
# SUMMARY
# -------------------------
print("\nDONE")
print(f"Saved: {saved}")
print(f"Failed: {failed}")
