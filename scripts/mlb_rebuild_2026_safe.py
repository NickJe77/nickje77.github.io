import requests
import json
import time
from pathlib import Path
from datetime import datetime, timezone

print("MLB 2026 SAFE REBUILD")

BASE = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASON = 2026
START_DATE = "2026-03-26"
TODAY_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%d")

OUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEAM_MAP = {
    108: "LAA", 109: "ARI", 110: "BAL", 111: "BOS", 112: "CHC",
    113: "CIN", 114: "CLE", 115: "COL", 116: "DET", 117: "HOU",
    118: "KC", 119: "LAD", 120: "WSH", 121: "NYM", 133: "OAK",
    134: "PIT", 135: "SD", 136: "SEA", 137: "SF", 138: "STL",
    139: "TB", 140: "TEX", 141: "TOR", 142: "MIN", 143: "PHI",
    144: "ATL", 145: "CWS", 146: "MIA", 147: "NYY", 158: "MIL",
}


# ✅ FIXED REQUEST HANDLING
def safe_get(url):
    for i in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)

            if r.status_code == 200:
                return r.json()

            print(f"Retry {i+1}: status {r.status_code}")

        except Exception as e:
            print(f"Retry {i+1} error: {e}")

        time.sleep(1)

    print(f"FAILED: {url}")
    return None


# ✅ DATE-BASED SCHEDULE (WORKING)
def get_schedule_games():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={TODAY_UTC}"
    data = safe_get(url)

    if not data:
        print("❌ No schedule returned")
        return []

    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):

            game_type = g.get("gameType", "")
            if game_type not in {"R", "P", "S"}:
                continue

            status = g.get("status", {}).get("codedGameState", "")
            if status not in {"F", "O", "I", "S"}:
                continue

            game_date = str(g.get("gameDate", ""))[:10]

            home_id = g["teams"]["home"]["team"]["id"]
            away_id = g["teams"]["away"]["team"]["id"]

            games.append({
                "gamePk": g["gamePk"],
                "date": game_date,
                "home": TEAM_MAP.get(home_id, "UNK"),
                "away": TEAM_MAP.get(away_id, "UNK"),
            })

    return games


def build_one_game(game):
    fname = f"{game['date']}_{game['away']}_{game['home']}.json"
    out_file = OUT_DIR / fname

    # keep your safety
    if out_file.exists():
        return "exists"

    full = safe_get(f"{BASE}/game/{game['gamePk']}/feed/live")

    # ✅ FIX: DO NOT STOP BUILD
    if not full:
        print(f"NO DATA — building empty shell: {game['date']} {game['away']} @ {game['home']}")
        full = {}

    teams = full.get("liveData", {}).get("boxscore", {}).get("teams", {})

    batting = []
    pitching = []

    for side in ["away", "home"]:
        players = teams.get(side, {}).get("players", {})

        for p in players.values():
            name = p.get("person", {}).get("fullName", "")
            stats = p.get("stats", {})

            b = stats.get("batting")
            if b:
                batting.append({
                    "team": side,
                    "name": name,
                    "AB": b.get("atBats", 0),
                    "R": b.get("runs", 0),
                    "H": b.get("hits", 0),
                    "RBI": b.get("rbi", 0),
                    "BB": b.get("baseOnBalls", 0),
                    "SO": b.get("strikeOuts", 0)
                })

            pit = stats.get("pitching")
            if pit:
                pitching.append({
                    "team": side,
                    "name": name,
                    "IP": pit.get("inningsPitched", "0.0"),
                    "H": pit.get("hits", 0),
                    "R": pit.get("runs", 0),
                    "ER": pit.get("earnedRuns", 0),
                    "BB": pit.get("baseOnBalls", 0),
                    "SO": pit.get("strikeOuts", 0)
                })

    data = {
        "game_id": f"{game['home']}{game['date'].replace('-', '')}0",
        "date": game["date"],
        "season": SEASON,
        "home_team": game["home"],
        "away_team": game["away"],
        "batting": batting,
        "pitching": pitching,
        "events": []
    }

    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    return "built"


def main():
    games = get_schedule_games()

    print(f"Found {len(games)} games")

    built = 0

    for game in games:
        result = build_one_game(game)

        if result == "built":
            built += 1
            print(f"Built: {game['date']} {game['away']} @ {game['home']}")

        time.sleep(0.2)

    print(f"\nDONE — Built {built} files")


if __name__ == "__main__":
    main()
