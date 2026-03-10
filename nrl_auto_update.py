import json
import requests
from pathlib import Path

SEASON = 2026
FILE = Path("docs/data/nrl/matches/2026.json")

URL = "https://www.nrl.com/fixtures/?competition=111&season=2026&round=all&format=json"

print("Downloading fixtures...")

res = requests.get(URL, timeout=30)

if res.status_code != 200:
    print("Fixture download failed")
    exit()

data = res.json()

with open(FILE) as f:
    rows = json.load(f)

existing = {r["match_id"] for r in rows}

added = 0

for match in data["matches"]:

    match_id = str(match["id"])

    if match_id in existing:
        continue

    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]

    home_score = match.get("homeScore", 0)
    away_score = match.get("awayScore", 0)

    row = {
        "season": SEASON,
        "match_id": match_id,
        "date_iso": match["date"][:10],
        "venue": match["venue"]["name"],
        "home_team": home,
        "away_team": away,
        "home_points": home_score,
        "away_points": away_score,
        "margin": abs(home_score-away_score),
        "total_points": home_score+away_score,
        "player":"",
        "played_for":"",
        "tries":0,
        "goals_made":0,
        "goals_attempted":0,
        "field_goals":0,
        "points":0
    }

    rows.append(row)
    added += 1

with open(FILE,"w") as f:
    json.dump(rows,f,indent=2)

print("Matches added:",added)
