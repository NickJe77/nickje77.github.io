import json
import requests
from pathlib import Path

SEASON = 2026

MATCH_FILE = Path("docs/data/nrl/matches/2026.json")

BASE = "https://www.nrl.com/draw/data"

with open(MATCH_FILE) as f:
    rows = json.load(f)

existing = {r["match_id"] for r in rows}

added = 0

url = f"{BASE}/{SEASON}.json"

res = requests.get(url, timeout=30)
data = res.json()

for rnd in data["rounds"]:

    for g in rnd["matches"]:

        match_id = str(g["matchId"])

        if match_id in existing:
            continue

        row = {
            "season": SEASON,
            "match_id": match_id,
            "date_iso": g["utcStartTime"][:10],
            "venue": g["venue"]["name"],
            "home_team": g["homeTeam"]["nickName"],
            "away_team": g["awayTeam"]["nickName"],
            "home_points": g["homeTeam"]["score"],
            "away_points": g["awayTeam"]["score"],
            "margin": abs(g["homeTeam"]["score"] - g["awayTeam"]["score"]),
            "total_points": g["homeTeam"]["score"] + g["awayTeam"]["score"],
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

with open(MATCH_FILE, "w") as f:
    json.dump(rows, f, indent=2)

print("Matches added:", added)
