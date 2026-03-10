import json
import requests
from pathlib import Path

FILE = Path("docs/data/nrl/matches/2026.json")

URL = "https://www.nrl.com/draw/data?competition=111&season=2026"

with open(FILE) as f:
    data = json.load(f)

existing = set()
for r in data:
    existing.add(r["match_id"])

res = requests.get(URL)
draw = res.json()

added = 0

for rnd in draw["rounds"]:
    for game in rnd["matches"]:

        match_id = str(game["matchId"])

        if match_id in existing:
            continue

        row = {
            "season": 2026,
            "match_id": match_id,
            "venue": game["venue"]["name"],
            "crowd": None,
            "date_iso": game["utcKickOffTime"][:10],
            "home_team": game["homeTeam"]["nickName"],
            "away_team": game["awayTeam"]["nickName"],
            "home_points": game.get("homeScore"),
            "away_points": game.get("awayScore"),
            "margin": None,
            "total_points": None,
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

with open(FILE, "w") as f:
    json.dump(data, f, indent=2)

print("Added matches:", added)
