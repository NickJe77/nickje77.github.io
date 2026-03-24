import requests
import json
from pathlib import Path
from datetime import datetime

print("MLB UPDATER (FINAL FIX)")

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
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            if g.get("gameType") not in ["R", "P"]:
                continue

            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["gameDate"][:10],
                "season": SEASON,
                "game_type": "Regular Season" if g["gameType"] == "R" else "Playoffs",
                "home_team": g["teams"]["home"]["team"]["name"],
                "away_team": g["teams"]["away"]["team"]["name"],
                "home_score": g["teams"]["home"].get("score", 0),
                "away_score": g["teams"]["away"].get("score", 0),
                "status": g["status"]["detailedState"],
                "state": g["status"]["abstractGameState"]   # 🔥 KEY FIELD
            })

    print("Games:", len(games))
    return games


# -------------------------
# GET BOXSCORE
# -------------------------
def get_boxscore(game_id):

    url = f"{BASE}/game/{game_id}/feed/live"

    try:
        data = requests.get(url, headers=HEADERS, timeout=10).json()
    except:
        print("❌ Failed:", game_id)
        return None

    try:
        teams = data["liveData"]["boxscore"]["teams"]
    except:
        print("❌ No data:", game_id)
        return None

    def parse(team):
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
    players += parse(teams["home"])
    players += parse(teams["away"])

    return players


# -------------------------
# RUN
# -------------------------
games = get_schedule()
all_games = []

for g in games:

    game_id = g["game_id"]

    print(f"{game_id} → {g['status']} ({g['state']})")

    # 🔥 ONLY FINISHED GAMES
    if g["state"] != "Final":
        continue

    file_path = BOX_DIR / f"{game_id}.json"

    print("⬇ Writing:", game_id)

    box = get_boxscore(game_id)

    if box:
        with open(file_path, "w") as f:
            json.dump(box, f, indent=2)
    else:
        print("❌ Empty:", game_id)

    all_games.append(g)


# -------------------------
# SAVE SEASON
# -------------------------
season_output = {
    "season": SEASON,
    "games": all_games,
    "updated": datetime.utcnow().isoformat()
}

with open(SEASON_DIR / f"{SEASON}.json", "w") as f:
    json.dump(season_output, f, indent=2)

print("DONE ✅")
