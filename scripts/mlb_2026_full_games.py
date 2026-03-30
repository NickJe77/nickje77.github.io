import requests
import json
from pathlib import Path
from datetime import datetime
import time

print("MLB 2026 FULL SCRAPER (FIXED)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

SEASON_DIR = Path("docs/data/baseball/seasons")
BOX_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")

SEASON_DIR.mkdir(parents=True, exist_ok=True)
BOX_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------
# GET FULL SCHEDULE (WITH MORE DATA)
# -----------------------------------
def get_schedule():
    url = (
        f"{BASE}/schedule?"
        f"sportId=1"
        f"&startDate={START_DATE}"
        f"&endDate={END_DATE}"
        f"&hydrate=team,linescore"
    )

    data = requests.get(url, headers=HEADERS).json()

    games = []

    for date in data.get("dates", []):
        for g in date.get("games", []):

            # ONLY REGULAR + POSTSEASON
            if g.get("gameType") not in ["R", "P"]:
                continue

            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["gameDate"],
                "home_team": g["teams"]["home"]["team"]["name"],
                "away_team": g["teams"]["away"]["team"]["name"],
                "status": g["status"]["detailedState"]
            })

    return games


# -----------------------------------
# GET FULL BOXSCORE (THIS IS THE KEY)
# -----------------------------------
def get_boxscore(game_id):
    url = f"{BASE}/game/{game_id}/boxscore"

    try:
        data = requests.get(url, headers=HEADERS).json()
    except:
        return None

    if "teams" not in data:
        return None

    game = {
        "game_id": game_id,
        "teams": {},
        "players": []
    }

    for side in ["home", "away"]:
        team = data["teams"][side]

        team_name = team["team"]["name"]

        game["teams"][side] = {
            "name": team_name,
            "runs": team.get("teamStats", {}).get("batting", {}).get("runs", 0),
            "hits": team.get("teamStats", {}).get("batting", {}).get("hits", 0),
            "errors": team.get("teamStats", {}).get("fielding", {}).get("errors", 0)
        }

        players = team.get("players", {})

        for pid, p in players.items():
            person = p.get("person", {})
            stats = p.get("stats", {})

            batting = stats.get("batting", {})
            pitching = stats.get("pitching", {})

            game["players"].append({
                "player_id": person.get("id"),
                "name": person.get("fullName"),
                "team": team_name,

                # batting
                "ab": batting.get("atBats"),
                "r": batting.get("runs"),
                "h": batting.get("hits"),
                "rbi": batting.get("rbi"),

                # pitching
                "ip": pitching.get("inningsPitched"),
                "er": pitching.get("earnedRuns"),
                "so": pitching.get("strikeOuts"),
            })

    return game


# -----------------------------------
# MAIN
# -----------------------------------
def run():
    games = get_schedule()
    print(f"Found {len(games)} games")

    season_games = []

    for g in games:
        gid = g["game_id"]

        outfile = BOX_DIR / f"{gid}.json"

        if outfile.exists():
            print(f"Skipping {gid}")
            continue

        print(f"Downloading {gid}")

        box = get_boxscore(gid)

        if not box:
            print("FAILED")
            continue

        with open(outfile, "w") as f:
            json.dump(box, f, indent=2)

        season_games.append(g)

        time.sleep(0.5)

    # SAVE SEASON INDEX
    with open(SEASON_DIR / f"{SEASON}.json", "w") as f:
        json.dump(season_games, f, indent=2)


if __name__ == "__main__":
    run()
