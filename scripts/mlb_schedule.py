import requests
import json
from pathlib import Path
from datetime import datetime

print("MLB SCHEDULE BUILDER (FIXED)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

OUT = Path(f"docs/data/baseball/seasons/{SEASON}.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}"
data = requests.get(url).json()

games = []

for date in data.get("dates", []):
    for g in date.get("games", []):

        # ✅ ONLY REAL GAMES
        if g.get("gameType") not in ["R", "P"]:
            continue

        games.append({
            "game_id": str(g["gamePk"]),
            "date": g["gameDate"],
            "home_team": g["teams"]["home"]["team"]["name"],
            "away_team": g["teams"]["away"]["team"]["name"],
            "status": g["status"]["detailedState"]
        })

# ✅ MATCH OLD STRUCTURE
output = {
    "season": SEASON,
    "games": games
}

print(f"{len(games)} games saved")

with open(OUT, "w") as f:
    json.dump(output, f, indent=2)
