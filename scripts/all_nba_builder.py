import requests
import json
from pathlib import Path
import re

print("ALL-NBA BUILDER (API VERSION)")

OUTPUT = Path("docs/data/nba/all_nba.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# 🔥 This endpoint contains the real data
URL = "https://cdn.nba.com/static/json/staticData/all_nba_teams.json"

res = requests.get(URL)
data_raw = res.json()

data = []

TEAM_MAP = {
    "Bucks":"MIL","Thunder":"OKC","Nuggets":"DEN","Cavaliers":"CLE","Celtics":"BOS",
    "Knicks":"NYK","Warriors":"GSW","Timberwolves":"MIN","Lakers":"LAL","Pistons":"DET",
    "Pacers":"IND","Clippers":"LAC","Mavericks":"DAL","Suns":"PHX","76ers":"PHI",
    "Heat":"MIA","Kings":"SAC","Trail Blazers":"POR","Raptors":"TOR","Bulls":"CHI",
    "Nets":"BKN","Hawks":"ATL","Jazz":"UTA","Wizards":"WAS","Pelicans":"NOP",
    "Hornets":"CHA","Grizzlies":"MEM","Spurs":"SAS","Rockets":"HOU","Magic":"ORL"
}

def abbr(team):
    return TEAM_MAP.get(team, team)

for season in data_raw.get("seasons", []):

    season_obj = {
        "season": season.get("season"),
        "first_team": [],
        "second_team": [],
        "third_team": []
    }

    for team in season.get("teams", []):
        team_type = team.get("teamType")  # FIRST / SECOND / THIRD

        key = None
        if team_type == "FIRST":
            key = "first_team"
        elif team_type == "SECOND":
            key = "second_team"
        elif team_type == "THIRD":
            key = "third_team"

        if not key:
            continue

        for player in team.get("players", []):
            season_obj[key].append({
                "player": player.get("name"),
                "team": abbr(player.get("teamName", ""))
            })

    data.append(season_obj)

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE: {len(data)} seasons saved")
