import json
import requests
from pathlib import Path

SEASON = 2026

FILE = Path("docs/data/nrl/matches/2026.json")

URL = f"https://www.nrl.com/draw/data/{SEASON}.json"

print("Downloading draw...")

res = requests.get(URL, timeout=30)

if res.status_code != 200:
    print("Draw download failed")
    exit()

data = res.json()

if "rounds" not in data:
    print("Rounds not found in response")
    exit()

with open(FILE) as f:
    rows = json.load(f)

existing = {r["match_id"] for r in rows}

added = 0

for rnd in data["rounds"]:

    for match in rnd["matches"]:

        match_id = str(match["matchId"])

        if match_id in existing:
            continue

        home = match["homeTeam"]
        away = match["awayTeam"]

        home_score = home.get("score", 0)
        away_score = away.get("score", 0)

        row = {
            "season": SEASON,
            "match_id": match_id,
            "date_iso": match["utcStartTime"][:10],
            "venue": match["venue"]["name"],
            "home_team": home["nickName"],
            "away_team": away["nickName"],
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
