import requests
import json
from pathlib import Path

print("ALL-NBA BUILDER (FINAL — NO BLOCKS)")

OUTPUT = Path("docs/data/nba/all_nba.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# ✅ Clean public dataset (stable)
URL = "https://raw.githubusercontent.com/abresler/nba-all-nba-teams/main/all_nba_teams.json"

res = requests.get(URL)
data_raw = res.json()

data = []

TEAM_MAP = {
    "BRK": "BKN",
    "CHO": "CHA"
}

for season in data_raw:

    season_obj = {
        "season": season["season"],
        "first_team": [],
        "second_team": [],
        "third_team": []
    }

    for team in season["teams"]:
        key = None

        if team["team"] == "First":
            key = "first_team"
        elif team["team"] == "Second":
            key = "second_team"
        elif team["team"] == "Third":
            key = "third_team"

        if not key:
            continue

        for player in team["players"]:
            season_obj[key].append({
                "player": player["name"],
                "team": TEAM_MAP.get(player.get("team", ""), player.get("team", ""))
            })

    data.append(season_obj)

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE: {len(data)} seasons saved")
