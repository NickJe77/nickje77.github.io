import json
import requests
from pathlib import Path

URL = "https://www.nrl.com/draw/data?competition=111&season=2026"

DATA_FILE = Path("docs/data/nrl/matches/2026.json")

if not DATA_FILE.exists():
    print("Data file not found")
    exit()

with open(DATA_FILE) as f:
    data = json.load(f)

existing = {row["match_id"] for row in data}

res = requests.get(URL)
draw = res.json()

for round in draw["rounds"]:
    for game in round["matches"]:

        match_id = str(game["matchId"])

        if match_id in existing:
            continue

        home = game["homeTeam"]["nickName"]
        away = game["awayTeam"]["nickName"]

        row = {
            "season": 2026,
            "match_id": match_id,
            "venue": game["venue"]["name"],
            "crowd": None,
            "date_iso": game["utcKickOffTime"][:10],
            "home_team": home,
            "away_team": away,
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

        print("Added match", match_id)

with open(DATA_FILE, "w") as f:
    json.dump(data, f, indent=2)

print("NRL update complete")
