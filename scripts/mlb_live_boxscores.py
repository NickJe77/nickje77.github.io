import requests
import json
from pathlib import Path
from datetime import datetime
import time

print("MLB 2026 REBUILD (FINAL FIX - NO SKIPS)")

BASE = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON = 2026
START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

OUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
OUT_DIR.mkdir(parents=True, exist_ok=True)


TEAM_MAP = {
    108:"LAA",109:"ARI",110:"BAL",111:"BOS",112:"CHC",113:"CIN",
    114:"CLE",115:"COL",116:"DET",117:"HOU",118:"KC",119:"LAD",
    120:"WSH",121:"NYM",133:"OAK",134:"PIT",135:"SD",136:"SEA",
    137:"SF",138:"STL",139:"TB",140:"TEX",141:"TOR",142:"MIN",
    143:"PHI",144:"ATL",145:"CWS",146:"MIA",147:"NYY",158:"MIL"
}


# -------------------------
# GET GAMES
# -------------------------
def get_games():

    url = f"{BASE}/schedule?sportId=1&season={SEASON}&gameType=R,P"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):

            game_date = g["gameDate"][:10]

            if game_date < START_DATE:
                continue

            if g.get("gameType") not in ["R", "P"]:
                continue

            status = g.get("status", {}).get("codedGameState")

            if status not in ["F", "O", "I"]:
                continue

            games.append({
                "gamePk": g["gamePk"],
                "date": game_date,
                "home": TEAM_MAP.get(g["teams"]["home"]["team"]["id"], "UNK"),
                "away": TEAM_MAP.get(g["teams"]["away"]["team"]["id"], "UNK")
            })

    print(f"FOUND {len(games)} GAMES")
    return games


# -------------------------
# GET DATA
# -------------------------
def get_game_data(gamePk):

    url = f"{BASE}/game/{gamePk}/feed/live"
    data = requests.get(url, headers=HEADERS).json()

    plays = data.get("liveData", {}).get("plays", {}).get("allPlays", [])

    # ✅ USE PLAYS IF AVAILABLE
    if plays:
        events = []

        for p in plays:
            try:
                inning = p["about"]["inning"]
                half = p["about"]["halfInning"]
                batter = p["matchup"]["batter"]["id"]
                result = p["result"]["eventType"]

                events.append([
                    "play",
                    str(inning),
                    "0" if half == "top" else "1",
                    str(batter),
                    result
                ])
            except:
                continue

        return events

    # 🔥 FALLBACK → BOXSCORE
    box = data.get("liveData", {}).get("boxscore", {}).get("teams", {})

    events = []

    for side in ["home", "away"]:
        players = box.get(side, {}).get("players", {})

        for p in players.values():
            try:
                pid = p["person"]["id"]

                events.append([
                    "play",
                    "0",
                    "0",
                    str(pid),
                    "appearance"
                ])
            except:
                continue

    return events


# -------------------------
# MAIN
# -------------------------
games = get_games()

built = 0

for g in games:

    fname = f"{g['date']}_{g['away']}_{g['home']}.json"
    out_file = OUT_DIR / fname

    if out_file.exists():
        continue

    print("Building", fname)

    events = get_game_data(g["gamePk"])

    if not events:
        print("Still empty, skipping")
        continue

    game_json = {
        "game_id": f"{g['home']}{g['date'].replace('-','')}0",
        "date": g["date"],
        "season": 2026,
        "home_code": g["home"],
        "away_code": g["away"],
        "home_team": g["home"],
        "away_team": g["away"],
        "events": events
    }

    with open(out_file, "w") as f:
        json.dump(game_json, f, indent=2)

    built += 1
    time.sleep(0.25)


print(f"DONE — BUILT {built} FILES")
