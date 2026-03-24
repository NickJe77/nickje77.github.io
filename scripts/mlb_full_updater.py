import requests
import json
from pathlib import Path
from datetime import datetime

print("MLB FULL UPDATER (CURRENT SEASON ONLY)")

# -------------------------
# CONFIG
# -------------------------
SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# 🔥 Opening Day (adjust yearly if needed)
START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

# Paths
SEASON_DIR = Path("docs/data/baseball/seasons")
BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")

SEASON_DIR.mkdir(parents=True, exist_ok=True)
BOX_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------
# GET SCHEDULE (CURRENT ONLY)
# -------------------------
def get_schedule():
    print(f"Downloading schedule from {START_DATE} to {END_DATE}...")

    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            # ✅ Only MLB games
            if g.get("gameType") not in ["R", "P"]:
                continue

            game_id = str(g["gamePk"])

            games.append({
                "game_id": game_id,
                "date": g["gameDate"][:10],
                "season": SEASON,
                "game_type": "Regular Season" if g["gameType"] == "R" else "Playoffs",
                "home_team": g["teams"]["home"]["team"]["name"],
                "away_team": g["teams"]["away"]["team"]["name"],
                "home_score": g["teams"]["home"].get("score", 0),
                "away_score": g["teams"]["away"].get("score", 0),
                "status": g["status"]["detailedState"]
            })

    print("Games found:", len(games))
    return games


# -------------------------
# GET BOXSCORE
# -------------------------
def get_boxscore(game_id):

    url = f"{BASE}/game/{game_id}/boxscore"

    try:
        data = requests.get(url, headers=HEADERS, timeout=10).json()
    except:
        print("Failed boxscore:", game_id)
        return None

    def parse_team(team):
        team_name = team["team"]["name"]
        players = []

        for p in team.get("players", {}).values():

            person = p.get("person", {})
            stats = p.get("stats", {}).get("batting", {})

            # Skip players with no stats
            if not stats:
                continue

            players.append({
                "player": person.get("fullName"),
                "team": team_name,
                "at_bats": stats.get("atBats", 0),
                "runs": stats.get("runs", 0),
                "hits": stats.get("hits", 0),
                "rbi": stats.get("rbi", 0),
                "home_runs": stats.get("homeRuns", 0),
                "walks": stats.get("baseOnBalls", 0),
                "strikeouts": stats.get("strikeOuts", 0)
            })

        return players

    players = []
    players += parse_team(data["teams"]["home"])
    players += parse_team(data["teams"]["away"])

    return players


# -------------------------
# RUN
# -------------------------
games = get_schedule()

all_games = []

for g in games:

    game_id = g["game_id"]
    print("Processing:", game_id)

    box = get_boxscore(game_id)

    if box:
        with open(BOX_DIR / f"{game_id}.json", "w") as f:
            json.dump(box, f, indent=2)

    all_games.append(g)


# -------------------------
# SAVE SEASON FILE
# -------------------------
season_output = {
    "season": SEASON,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "games": all_games,
    "updated": datetime.utcnow().isoformat()
}

with open(SEASON_DIR / f"{SEASON}.json", "w") as f:
    json.dump(season_output, f, indent=2)

print("MLB UPDATE COMPLETE")
