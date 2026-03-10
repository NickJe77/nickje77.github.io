import json
import requests
from pathlib import Path

FILE = Path("docs/data/nrl/matches/2026.json")

URL = "https://d.flashscore.com/x/feed/f_1_111_1"

headers = {
    "User-Agent": "Mozilla/5.0",
    "X-Fsign": "SW9D1eZo"
}

print("Downloading Flashscore feed")

res = requests.get(URL, headers=headers)

text = res.text

matches = []

for line in text.splitlines():
    if line.startswith("AA"):
        parts = line.split("¬")
        match_id = parts[0][2:]
        matches.append(match_id)

print("Match IDs found:", len(matches))

with open(FILE) as f:
    rows = json.load(f)

existing = {r["match_id"] for r in rows}

added = 0

for mid in matches:

    if mid in existing:
        continue

    row = {
        "season": 2026,
        "match_id": mid,
        "date_iso": "",
        "venue": "",
        "home_team": "",
        "away_team": "",
        "home_points": 0,
        "away_points": 0,
        "margin": 0,
        "total_points": 0,
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
