import requests
import json
from pathlib import Path
from datetime import datetime

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

OUTPUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

# -----------------------------------------
# SAFE TEAM CODE GETTER
# -----------------------------------------
def get_team_code(team):
    return (
        team.get("abbreviation")
        or team.get("teamCode")
        or team.get("fileCode")
        or team.get("name", "")[:3].upper()
    )

# -----------------------------------------
# GET SCHEDULE
# -----------------------------------------
def get_games():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):

            if g.get("gameType") not in ["R", "P"]:
                continue

            home_team = g["teams"]["home"]["team"]
            away_team = g["teams"]["away"]["team"]

            games.append({
                "gamePk": g["gamePk"],
                "date": g["gameDate"][:10],
                "home": get_team_code(home_team),
                "away": get_team_code(away_team)
            })

    return games


# -----------------------------------------
# BUILD GAME
# -----------------------------------------
def build_game(game):
    url = f"{BASE}/game/{game['gamePk']}/playByPlay"
    data = requests.get(url, headers=HEADERS).json()

    events = []

    for play in data.get("allPlays", []):
        about = play.get("about", {})
        matchup = play.get("matchup", {})
        result = play.get("result", {})

        inning = str(about.get("inning", ""))
        half = "0" if about.get("halfInning") == "top" else "1"

        batter = matchup.get("batter", {}).get("id", "unknown")
        desc = result.get("event", "")

        events.append([
            "play",
            inning,
            half,
            str(batter),
            "00",
            "",
            desc
        ])

    return {
        "game_id": f"{game['away']}{game['date'].replace('-','')}0",
        "date": game["date"],
        "season": SEASON,
        "home_code": game["home"],
        "away_code": game["away"],
        "home_team": game["home"],
        "away_team": game["away"],
        "events": events
    }


# -----------------------------------------
# MAIN
# -----------------------------------------
print("BUILDING LIVE MLB DATA...")

games = get_games()

for g in games:
    try:
        game_data = build_game(g)

        out_file = OUTPUT_DIR / f"{game_data['game_id']}.json"

        with open(out_file, "w") as f:
            json.dump(game_data, f)

        print(f"Saved {game_data['game_id']}")

    except Exception as e:
        print(f"Error {g['gamePk']}: {e}")

print("DONE ✅")
