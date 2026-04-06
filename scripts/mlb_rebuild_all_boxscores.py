import requests
import json
from pathlib import Path
import time

print("MLB FULL HISTORY REBUILD (SAFE)")

BASE = "https://statsapi.mlb.com/api/v1.1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASONS = list(range(1947, 2027))

BOX_ROOT = Path("docs/data/baseball/boxscores")
BOX_ROOT.mkdir(parents=True, exist_ok=True)

def get_schedule(year):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&season={year}"
    data = requests.get(url, headers=HEADERS).json()

    games = []
    for d in data.get("dates", []):
        for g in d.get("games", []):
            if g.get("gameType") not in ["R", "P"]:
                continue

            games.append({
                "game_id": str(g["gamePk"]),
                "date": g["gameDate"][:10],
                "home": g["teams"]["home"]["team"],
                "away": g["teams"]["away"]["team"]
            })

    print(f"{year}: {len(games)} games")
    return games

def extract_batting(team):
    out = []
    for p in team["players"].values():
        stats = p.get("stats", {}).get("batting")
        if not stats:
            continue
        out.append({
            "player_id": str(p["person"]["id"]),  # 🔥 REAL ID
            "AB": stats.get("atBats", 0),
            "H": stats.get("hits", 0),
            "HR": stats.get("homeRuns", 0)
        })
    return out

def extract_pitching(team):
    out = []
    for p in team["players"].values():
        stats = p.get("stats", {}).get("pitching")
        if not stats:
            continue
        out.append({
            "player_id": str(p["person"]["id"]),
            "IP": stats.get("inningsPitched", "0.0"),
            "H": stats.get("hits", 0),
            "ER": stats.get("earnedRuns", 0),
            "SO": stats.get("strikeOuts", 0)
        })
    return out

def build_game(year, game):

    game_id = game["game_id"]

    url = f"{BASE}/game/{game_id}/feed/live"
    data = requests.get(url, headers=HEADERS).json()

    box = data["liveData"]["boxscore"]["teams"]
    linescore = data["liveData"].get("linescore", {})
    gameData = data.get("gameData", {})

    home_team = game["home"]
    away_team = game["away"]

    home_code = home_team.get("abbreviation")
    away_code = away_team.get("abbreviation")

    venue = gameData.get("venue", {}).get("name")
    away_score = linescore.get("teams", {}).get("away", {}).get("runs")
    home_score = linescore.get("teams", {}).get("home", {}).get("runs")

    season_dir = BOX_ROOT / str(year)
    season_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{game['date']}_{away_code}_{home_code}.json"

    with open(season_dir / file_name, "w") as f:
        json.dump({
            "game_id": game_id,
            "date": game["date"],
            "season": year,
            "home_code": home_code,
            "away_code": away_code,
            "home_team": home_team.get("name"),
            "away_team": away_team.get("name"),
            "venue": venue,
            "away_score": away_score,
            "home_score": home_score,
            "batters_home": extract_batting(box["home"]),
            "batters_away": extract_batting(box["away"]),
            "pitchers_home": extract_pitching(box["home"]),
            "pitchers_away": extract_pitching(box["away"])
        }, f, indent=2)

    return file_name

def build_season(year):

    games = get_schedule(year)
    index = {}

    for g in games:
        try:
            file = build_game(year, g)
            index[g["game_id"]] = file
            time.sleep(0.2)
        except Exception as e:
            print(f"FAIL {g['game_id']}:", e)

    with open(BOX_ROOT / str(year) / "index.json", "w") as f:
        json.dump(index, f, indent=2)

for year in SEASONS:
    build_season(year)

print("FULL REBUILD COMPLETE")
