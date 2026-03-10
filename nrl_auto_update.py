import json
import requests
from pathlib import Path

FILE = Path("docs/data/nrl/matches/2026.json")
URL = "https://www.nrl.com/draw/data?competition=111&season=2026"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

with open(FILE) as f:
    data = json.load(f)

existing = {r["match_id"] for r in data if "match_id" in r}

res = requests.get(URL, headers=headers)

try:
    draw = res.json()
except Exception:
    print("NRL endpoint did not return JSON")
    exit()

rounds = draw.get("rounds", [])
if not rounds:
    print("No rounds found in response")
    exit()

added = 0

for rnd in rounds:
    matches = rnd.get("matches", [])
    for game in matches:

        match_id = str(game.get("matchId", ""))

        if not match_id or match_id in existing:
            continue

        home = game.get("homeTeam", {}).get("nickName", "")
        away = game.get("awayTeam", {}).get("nickName", "")

        home_score = game.get("homeScore", 0)
        away_score = game.get("awayScore", 0)

        venue = game.get("venue", {}).get("name", "")
        date_iso = game.get("utcKickOffTime", "")[:10]

        row = {
            "season": 2026,
            "match_id": match_id,
            "venue": venue,
            "crowd": None,
            "date_iso": date_iso,
            "home_team": home,
            "away_team": away,
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

        data.append(row)
        added += 1

with open(FILE, "w") as f:
    json.dump(data, f, indent=2)

print("Matches added:", added)
