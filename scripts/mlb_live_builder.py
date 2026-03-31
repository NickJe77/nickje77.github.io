import requests
import json
from pathlib import Path
from datetime import datetime

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

OUTPUT_DIR = Path(f"docs/data/baseball/games/{SEASON}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

def get_games():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
    data = requests.get(url, headers=HEADERS).json()

    games = []

    for d in data.get("dates", []):
        for g in d.get("games", []):
            if g.get("gameType") not in ["R","P"]:
                continue

            games.append({
                "gamePk": g["gamePk"],
                "date": g["gameDate"][:10]
            })

    return games

def extract_batting(players):
    out=[]
    for pid,p in players.items():
        if "stats" not in p: continue
        b=p["stats"].get("batting",{})
        if not b: continue

        out.append({
            "player_id": str(p["person"]["id"]),
            "AB": b.get("atBats",0),
            "R": b.get("runs",0),
            "H": b.get("hits",0),
            "RBI": b.get("rbi",0),
            "BB": b.get("baseOnBalls",0),
            "SO": b.get("strikeOuts",0)
        })
    return out

def extract_pitching(players):
    out=[]
    for pid,p in players.items():
        if "stats" not in p: continue
        pit=p["stats"].get("pitching",{})
        if not pit: continue

        out.append({
            "player_id": str(p["person"]["id"]),
            "IP": pit.get("inningsPitched","0"),
            "H": pit.get("hits",0),
            "R": pit.get("runs",0),
            "ER": pit.get("earnedRuns",0),
            "BB": pit.get("baseOnBalls",0),
            "SO": pit.get("strikeOuts",0)
        })
    return out

def build_game(game):

    url=f"{BASE}/game/{game['gamePk']}/boxscore"
    data=requests.get(url,headers=HEADERS).json()

    home=data["teams"]["home"]
    away=data["teams"]["away"]

    home_code=home["team"]["abbreviation"]
    away_code=away["team"]["abbreviation"]

    game_id=f"{home_code}{game['date'].replace('-','')}0"

    return {
        "game_id": game_id,
        "date": game["date"],
        "season": SEASON,
        "home_code": home_code,
        "away_code": away_code,
        "home_team": home_code,
        "away_team": away_code,

        "batters_home": extract_batting(home["players"]),
        "batters_away": extract_batting(away["players"]),
        "pitchers_home": extract_pitching(home["players"]),
        "pitchers_away": extract_pitching(away["players"])
    }

print("BUILDING MLB BOXSCORES...")

games=get_games()

for g in games:
    try:
        game_data=build_game(g)

        out=OUTPUT_DIR / f"{game_data['game_id']}.json"

        with open(out,"w") as f:
            json.dump(game_data,f)

        print("Saved",game_data["game_id"])

    except Exception as e:
        print("Error",g["gamePk"],e)

print("DONE")
