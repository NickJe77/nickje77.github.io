import requests
import json
from pathlib import Path
from datetime import datetime
import time
import re

print("MLB 2026 REBUILD (FINAL WITH INDEX)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1.1"

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
BOX_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# 🔥 INDEX MAP (GAME ID → FILE)
INDEX = {}


# -------------------------------------------------
# PLAYER CODE
# -------------------------------------------------
def make_player_code(name):
    try:
        name = re.sub(r"[^\w\s]", "", name.lower())
        parts = name.split()

        if len(parts) < 2:
            return "unknown001"

        first = parts[0]
        last = parts[-1]

        return f"{last[:5]}{first[:2]}001"

    except:
        return "unknown001"


# -------------------------------------------------
# TEAM CODE
# -------------------------------------------------
def get_team_code(team):
    return (
        team.get("abbreviation")
        or team.get("teamCode")
        or team.get("fileCode")
        or team.get("name", "")[:3].upper()
    )


# -------------------------------------------------
# GET SCHEDULE (FILTERED)
# -------------------------------------------------
def get_schedule():
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            # 🔥 ONLY REGULAR + POSTSEASON
            game_type = g.get("gameType")
            if game_type not in ["R", "P"]:
                continue

            gamePk = str(g["gamePk"])
            gameDate = g["gameDate"][:10]

            home = get_team_code(g["teams"]["home"]["team"])
            away = get_team_code(g["teams"]["away"]["team"])

            games.append({
                "game_id": gamePk,
                "date": gameDate,
                "home": home,
                "away": away
            })

    print(f"FOUND {len(games)} VALID GAMES")
    return games


# -------------------------------------------------
# BUILD GAME
# -------------------------------------------------
def build_game(game):

    game_id = game["game_id"]
    url = f"{BASE}/game/{game_id}/feed/live"

    try:
        data = requests.get(url, headers=HEADERS, timeout=20).json()
    except:
        print(f"❌ FAILED REQUEST {game_id}")
        return False

    try:
        plays = data["liveData"]["plays"]["allPlays"]

        events = []

        for p in plays:

            about = p.get("about", {})
            matchup = p.get("matchup", {})
            result = p.get("result", {})
            count_data = p.get("count", {})

            inning = str(about.get("inning", ""))
            half = "1" if about.get("isTopInning", True) else "0"

            batter_name = matchup.get("batter", {}).get("fullName", "")
            batter_code = make_player_code(batter_name)

            balls = count_data.get("balls", 0)
            strikes = count_data.get("strikes", 0)

            count = f"{balls}{strikes}"
            event = result.get("event", "")

            events.append([
                "play",
                inning,
                half,
                batter_code,
                count,
                event
            ])

        file_name = f"{game['date']}_{game['away']}_{game['home']}.json"
        file_path = BOX_DIR / file_name

        # 🔥 WRITE FILE
        with open(file_path, "w") as f:
            json.dump({
                "game_id": game_id,
                "date": game["date"],
                "season": SEASON,
                "home_code": game["home"],
                "away_code": game["away"],
                "home_team": game["home"],
                "away_team": game["away"],
                "events": events
            }, f, indent=2)

        # 🔥 ADD TO INDEX
        INDEX[game_id] = file_name

        print(f"✅ SAVED {file_name}")
        return True

    except Exception as e:
        print(f"❌ PARSE ERROR {game_id}: {e}")
        return False


# -------------------------------------------------
# MAIN
# -------------------------------------------------
games = get_schedule()

if not games:
    print("❌ NO GAMES FOUND")
    exit()

saved = 0

for g in games:
    if build_game(g):
        saved += 1

    time.sleep(0.3)

# 🔥 BUILD INDEX FILE
index_path = BOX_DIR / "index.json"

with open(index_path, "w") as f:
    json.dump(INDEX, f, indent=2)

print(f"📦 INDEX BUILT ({len(INDEX)} games)")
print(f"🎯 DONE — {saved} FILES WRITTEN")
