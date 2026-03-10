import requests
import json
import os
from datetime import datetime

print("NBA updater starting")

OUTPUT_DIR = "docs/data/nba/2026"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# NBA official games endpoint
SCHEDULE_URL = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"

r = requests.get(SCHEDULE_URL)

if r.status_code != 200:
    print("Failed to load schedule")
    exit()

data = r.json()

games = data["leagueSchedule"]["gameDates"]

games_found = 0
games_saved = 0

for date in games:

    for game in date["games"]:

        game_id = game["gameId"]

        # skip if file already exists
        file_path = f"{OUTPUT_DIR}/{game_id}.json"
        if os.path.exists(file_path):
            continue

        games_found += 1

        box_url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

        box = requests.get(box_url)

        if box.status_code != 200:
            continue

        box = box.json()

        g = box["game"]

        output = {
            "game_id": game_id,
            "date": g["gameTimeUTC"],
            "home_team": g["homeTeam"]["teamName"],
            "away_team": g["awayTeam"]["teamName"],
            "home_score": g["homeTeam"]["score"],
            "away_score": g["awayTeam"]["score"],
            "arena": g["arena"]["arenaName"],
            "players": []
        }

        for team in ["homeTeam","awayTeam"]:

            team_name = g[team]["teamName"]

            for p in g[team]["players"]:

                stats = p.get("statistics", {})

                output["players"].append({
                    "player": p["name"],
                    "team": team_name,
                    "points": stats.get("points",0),
                    "rebounds": stats.get("reboundsTotal",0),
                    "assists": stats.get("assists",0),
                    "minutes": stats.get("minutes","0")
                })

        with open(file_path,"w") as f:
            json.dump(output,f,indent=2)

        games_saved += 1
        print("Saved", file_path)

print("Games checked:", games_found)
print("Games saved:", games_saved)
print("NBA update finished")
