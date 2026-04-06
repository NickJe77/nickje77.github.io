import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

print("MLB INCREMENTAL FAST BUILD")

BASE = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

SEASONS = list(range(1947, 2027))
BOX_ROOT = Path("docs/data/baseball/boxscores")


# -----------------------------
# DATE RANGE
# -----------------------------
def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


# -----------------------------
# TEAM CODE (FIXED)
# -----------------------------
def get_team_code(t):
    return (
        t["team"].get("abbreviation")
        or t["team"].get("teamCode")
        or t["team"].get("fileCode")
        or t["team"].get("name", "")[:3].upper()
    )


# -----------------------------
# BATTING
# -----------------------------
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


# -----------------------------
# PITCHING
# -----------------------------
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


# -----------------------------
# BUILD SEASON
# -----------------------------
def build_season(year):

    print(f"=== {year} ===")

    season_dir = BOX_ROOT / str(year)
    season_dir.mkdir(parents=True, exist_ok=True)

    # load existing index
    index_path = season_dir / "index.json"
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {}

    existing_files = set(index.values())

    start = datetime(year, 3, 1)
    end = datetime(year, 11, 30)

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

                try:
                    home = g["teams"]["home"]
                    away = g["teams"]["away"]

                    home_code = get_team_code(home)
                    away_code = get_team_code(away)

                    file_name = f"{date_str}_{away_code}_{home_code}.json"

                    # 🔥 SKIP EXISTING
                    if file_name in existing_files:
                        continue

                    game_id = str(g["gamePk"])

                    with open(season_dir / file_name, "w") as f:
                        json.dump({
                            "game_id": game_id,
                            "date": date_str,
                            "season": year,
                            "home_code": home_code,
                            "away_code": away_code,
                            "home_team": home["team"].get("name"),
                            "away_team": away["team"].get("name"),
                            "venue": g.get("venue", {}).get("name"),
                            "away_score": g.get("linescore", {}).get("teams", {}).get("away", {}).get("runs"),
                            "home_score": g.get("linescore", {}).get("teams", {}).get("home", {}).get("runs"),
                            "batters_home": extract_batting(home),
                            "batters_away": extract_batting(away),
                            "pitchers_home": extract_pitching(home),
                            "pitchers_away": extract_pitching(away)
                        }, f, indent=2)

                    index[game_id] = file_name

                except Exception as e:
                    continue

        time.sleep(0.05)

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)


# -----------------------------
# RUN ALL
# -----------------------------
for y in SEASONS:
    build_season(y)

print("INCREMENTAL BUILD COMPLETE")
