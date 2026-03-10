import json
import requests
import re
from pathlib import Path

FILE = Path("docs/data/nrl/matches/2026.json")

URL = "https://www.rugbyleagueproject.org/seasons/nrl-2026/results.html"

print("Downloading Rugby League Project results")

html = requests.get(URL).text

matches = re.findall(r'/seasons/nrl-2026/round-[0-9]+/.+?/summary.html', html)

print("Matches found:", len(matches))

with open(FILE) as f:
    rows = json.load(f)

existing = {r["match_id"] for r in rows}

added = 0

for m in matches:

    match_id = m.split("/")[-2]

    if match_id in existing:
        continue

    row = {
        "season": 2026,
        "match_id": match_id,
        "date_iso": "",
        "venue": "",
        "home_team": "",
        "away_team": "",
        "home_points": 0,
        "away_points": 0,
        "margin": 0,
        "total_points": 0,
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
