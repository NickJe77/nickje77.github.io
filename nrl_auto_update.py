import json
import requests
from pathlib import Path

SEASON = 2026
FILE = Path("docs/data/nrl/matches/2026.json")

URL = "https://site.api.espn.com/apis/site/v2/sports/rugby-league/nrl/scoreboard?limit=1000"

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("Downloading scoreboard")

res = requests.get(URL, headers=headers, timeout=30)

data = res.json()
events = data.get("events", [])

if not events:
    print("No games returned from ESPN")
    exit()

with open(FILE) as f:
    rows = json.load(f)

existing = {r["match_id"] for r in rows}

added = 0

for g in events:

    match_id = g["id"]

    if match_id in existing:
        continue

    comp = g["competitions"][0]

    home = next(t for t in comp["competitors"] if t["homeAway"] == "home")
    away = next(t for t in comp["competitors"] if t["homeAway"] == "away")

    home_team = home["team"]["displayName"]
    away_team = away["team"]["displayName"]

    home_score = int(home.get("score", 0))
    away_score = int(away.get("score", 0))

    venue = comp.get("venue", {}).get("fullName", "")

    row = {
        "season": SEASON,
        "match_id": match_id,
        "date_iso": g["date"][:10],
        "venue": venue,
        "home_team": home_team,
        "away_team": away_team,
        "home_points": home_score,
        "away_points": away_score,
        "margin": abs(home_score - away_score),
        "total_points": home_score + away_score,
        "player": "",
        "played_for": "",
        "tries": 0,
        "goals_made": 0,
        "goals_attempted": 0,
        "field_goals": 0,
        "points": 0
    }

    rows.append(row)
    added += 1

with open(FILE, "w") as f:
    json.dump(rows, f, indent=2)

print("Matches added:", added)
