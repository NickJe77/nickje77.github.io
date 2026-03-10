import json
import requests
from pathlib import Path

FILE = Path("docs/data/nrl/matches/2026.json")

URL = "https://site.api.espn.com/apis/site/v2/sports/rugby-league/nrl/scoreboard"

with open(FILE) as f:
    data = json.load(f)

existing = {r["match_id"] for r in data}

res = requests.get(URL)

games = res.json().get("events", [])

added = 0

for game in games:

    match_id = game["id"]

    if match_id in existing:
        continue

    comp = game["competitions"][0]

    home = comp["competitors"][0]
    away = comp["competitors"][1]

    home_team = home["team"]["displayName"]
    away_team = away["team"]["displayName"]

    home_score = int(home.get("score",0))
    away_score = int(away.get("score",0))

    venue = comp.get("venue",{}).get("fullName","")
    date = game["date"][:10]

    row = {
        "season": 2026,
        "match_id": match_id,
        "venue": venue,
        "crowd": None,
        "date_iso": date,
        "home_team": home_team,
        "away_team": away_team,
        "home_points": home_score,
        "away_points": away_score,
        "margin": abs(home_score-away_score),
        "total_points": home_score+away_score,
        "player": "",
        "played_for": "",
        "tries": 0,
        "goals_made": 0,
        "goals_attempted": 0,
        "field_goals": 0,
        "points": 0
    }

    data.append(row)
    added += 1

with open(FILE,"w") as f:
    json.dump(data,f,indent=2)

print("Matches added:",added)
