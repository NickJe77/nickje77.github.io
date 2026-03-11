import json
import requests
import csv
from pathlib import Path
from io import StringIO

URL = "https://www.rugbyleagueproject.org/seasons/nrl-2026/results.csv"

OUT = Path("docs/data/nrl/matches/2026.json")

print("Downloading NRL results CSV")

r = requests.get(URL)

if r.status_code != 200:
    print("Download failed:", r.status_code)
    exit()

data = list(csv.DictReader(StringIO(r.text)))

rows = []

for g in data:

    try:
        home = g["Home Team"]
        away = g["Away Team"]
        home_points = int(g["Home Score"])
        away_points = int(g["Away Score"])
        venue = g["Venue"]
        date = g["Date"]
    except:
        continue

    rows.append({
        "season": 2026,
        "match_id": f"{date}-{home}-{away}",
        "date_iso": "",
        "venue": venue,
        "home_team": home,
        "away_team": away,
        "home_points": home_points,
        "away_points": away_points,
        "margin": abs(home_points - away_points),
        "total_points": home_points + away_points,
        "player": "",
        "played_for": "",
        "tries": 0,
        "goals_made": 0,
        "goals_attempted": 0,
        "field_goals": 0,
        "points": 0
    })

print("Matches collected:", len(rows))

OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(rows, f, indent=2)

print("NRL data rebuilt successfully")
