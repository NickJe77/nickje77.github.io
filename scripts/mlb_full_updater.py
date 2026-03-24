import requests
import json
from pathlib import Path
from datetime import datetime

print("MLB FULL UPDATER (FIXED BOXSCORES)")

# -------------------------
# CONFIG
# -------------------------
SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

SEASON_DIR = Path("docs/data/baseball/seasons")
BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")

SEASON_DIR.mkdir(parents=True, exist_ok=True)
BOX_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------
# GET SCHEDULE
# -------------------------
def get_schedule():
    print(f"Schedule: {START_DATE} → {END_DATE}")

    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            if g.get("gameType") not in ["R", "P"]:
                continue

            status = g["status"]["detailedState"]

            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["gameDate"][:10],
                "season": SEASON,
                "game_type": "Regular Season" if g["gameType"] == "R" else "Playoffs",
                "home_team": g["teams"]["home"]["team"]["name"],
                "away_team": g["teams"]["away"]["team"]["name"],
                "home_score": g["teams"]["home"].get("score", 0),
                "away_score": g["teams"]["away"].get("score", 0),
                "status": status
            })

    print("Games found:", len(games))
    return games


# -------------------------
# CHECK IF GAME IS FINAL
# -------------------------
def is_final(status):
    return status in ["Final", "Game Over", "Completed Early"]


# -------------------------
# GET BOXSCORE
# -------------------------
def get_boxscore(game_id):

    url = f"{BASE}/game/{game_id}/boxscore"

    try:
        data = requests.get(url, headers=HEADERS, timeout=10).json()
    except:
        print("❌ Failed:", game_id)
        return None

    def parse_team(team):
        team_name = team["team"]["name"]
        players = []

        for p in team.get("players", {}).values():

            person = p.get("person", {})
            stats = p.get("stats", {}).get("batting", {})

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
    status = g["status"]

    print(f"{game_id} → {status}")

    # 🔥 ONLY FINISHED GAMES
    if not is_final(status):
        continue

    # 🔥 SKIP IF ALREADY EXISTS
    file_path = BOX_DIR / f"{game_id}.json"
    if file_path.exists():
        print("✔ Already exists:", game_id)
        all_games.append(g)
        continue

    print("⬇ Downloading:", game_id)

    box = get_boxscore(game_id)

    if box:
        with open(file_path, "w") as f:
            json.dump(box, f, indent=2)

    all_games.append(g)


# -------------------------
# SAVE SEASON
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

print("DONE ✅")
