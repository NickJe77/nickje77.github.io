import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

print("MLB FAST FULL HISTORY BUILD")

BASE = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASONS = list(range(1947, 2027))
BOX_ROOT = Path("docs/data/baseball/boxscores")

def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def extract_batting(team):
    out = []
    for p in team.get("players", {}).values():
        stats = p.get("stats", {}).get("batting")
        if not stats:
            continue
        out.append({
            "player_id": str(p["person"]["id"]),
            "AB": stats.get("atBats", 0),
            "H": stats.get("hits", 0),
            "HR": stats.get("homeRuns", 0)
        })
    return out

def extract_pitching(team):
    out = []
    for p in team.get("players", {}).values():
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

def build_season(year):

    print(f"\n=== {year} ===")

    start = datetime(year, 3, 1)
    end = datetime(year, 11, 30)

    season_dir = BOX_ROOT / str(year)
    season_dir.mkdir(parents=True, exist_ok=True)

    index = {}

    for d in daterange(start, end):

        date_str = d.strftime("%Y-%m-%d")

        url = f"{BASE}/schedule?sportId=1&date={date_str}&hydrate=boxscore,linescore"

        try:
            data = requests.get(url, headers=HEADERS).json()
        except:
            continue

        for day in data.get("dates", []):
            for g in day.get("games", []):

                if g.get("gameType") not in ["R", "P"]:
                    continue

                game_id = str(g["gamePk"])

                box = g.get("teams", {})
                linescore = g.get("linescore", {})

                try:
                    box_full = g["teams"]
                    home = box_full["home"]
                    away = box_full["away"]

                    file_name = f"{date_str}_{away['team']['abbreviation']}_{home['team']['abbreviation']}.json"

                    with open(season_dir / file_name, "w") as f:
                        json.dump({
                            "game_id": game_id,
                            "date": date_str,
                            "season": year,
                            "home_code": home["team"]["abbreviation"],
                            "away_code": away["team"]["abbreviation"],
                            "home_team": home["team"]["name"],
                            "away_team": away["team"]["name"],
                            "venue": g.get("venue", {}).get("name"),
                            "away_score": linescore.get("teams", {}).get("away", {}).get("runs"),
                            "home_score": linescore.get("teams", {}).get("home", {}).get("runs"),
                            "batters_home": extract_batting(home),
                            "batters_away": extract_batting(away),
                            "pitchers_home": extract_pitching(home),
                            "pitchers_away": extract_pitching(away)
                        }, f, indent=2)

                    index[game_id] = file_name

                except Exception as e:
                    continue

        time.sleep(0.1)

    with open(season_dir / "index.json", "w") as f:
        json.dump(index, f, indent=2)

for y in SEASONS:
    build_season(y)

print("FAST BUILD COMPLETE")
