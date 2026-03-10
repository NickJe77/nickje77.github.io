import json
import requests
import re
from pathlib import Path

FILE = Path("docs/data/nrl/matches/2026.json")

URL = "https://www.flashscore.com.au/rugby-league/australia/nrl/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("Downloading Flashscore NRL page")

html = requests.get(URL, headers=headers).text

# Flashscore embeds match ids in the page JSON
match_ids = re.findall(r'"id":"([A-Za-z0-9]{8})"', html)

print("Match IDs found:", len(match_ids))

with open(FILE) as f:
    rows = json.load(f)

existing = {r["match_id"] for r in rows}

added = 0

for mid in match_ids:

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
