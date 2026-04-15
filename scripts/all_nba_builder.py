import pandas as pd
import json
from pathlib import Path

print("ALL-NBA BUILDER (FINAL WORKING VERSION)")

OUTPUT = Path("docs/data/nba/all_nba.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

URL = "https://www.basketball-reference.com/awards/all_nba.html"

tables = pd.read_html(URL)
df = tables[0]

data = []
current_season = None
season_obj = None

TEAM_MAP = {
    "BRK": "BKN",
    "CHO": "CHA"
}

for _, row in df.iterrows():

    season = row["Season"]
    team_type = row["Lg"]

    if season != current_season:
        if season_obj:
            data.append(season_obj)

        season_obj = {
            "season": season,
            "first_team": [],
            "second_team": [],
            "third_team": []
        }
        current_season = season

    key = None
    if team_type == "1st":
        key = "first_team"
    elif team_type == "2nd":
        key = "second_team"
    elif team_type == "3rd":
        key = "third_team"

    if not key:
        continue

    players = [
        row["Player 1"], row["Player 2"], row["Player 3"],
        row["Player 4"], row["Player 5"]
    ]

    teams = [
        row["Tm 1"], row["Tm 2"], row["Tm 3"],
        row["Tm 4"], row["Tm 5"]
    ]

    for p, t in zip(players, teams):
        if pd.notna(p):
            team = TEAM_MAP.get(t, t)

            season_obj[key].append({
                "player": str(p),
                "team": str(team)
            })

if season_obj:
    data.append(season_obj)

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE: {len(data)} seasons saved")
