import requests
import json
import os
from datetime import datetime, timedelta

START_DATE = datetime(2026,2,16)
TODAY = datetime.utcnow()

OUTPUT_DIR = "docs/data/nba/2026"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("NBA updater starting")

date = START_DATE

while date <= TODAY:

    ds = date.strftime("%Y%m%d")

    url = f"https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_{ds}.json"

    r = requests.get(url)

    if r.status_code != 200:
        print("No schedule:", ds)
        date += timedelta(days=1)
        continue

    data = r.json()

    games = data.get("leagueSchedule",{}).get("gameDates",[])

    for d in games:

        for g in d.get("games",[]):

            game_id = g["gameId"]

            file_path = f"{OUTPUT_DIR}/{game_id}.json"

            if os.path.exists(file_path):
                continue

            box_url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

            b = requests.get(box_url)

            if b.status_code != 200:
                print("Boxscore missing:", game_id)
                continue

            box = b.json()["game"]

            output = {
                "game_id": game_id,
                "season": 2026,
                "date": box["gameTimeUTC"],
                "home_team": box["homeTeam"]["teamName"],
                "away_team": box["awayTeam"]["teamName"],
                "home_score": box["homeTeam"]["score"],
                "away_score": box["awayTeam"]["score"],
                "arena": box["arena"]["arenaName"],
                "players":[]
            }

            for team in ["homeTeam","awayTeam"]:

                team_name = box[team]["teamName"]

                for p in box[team]["players"]:

                    stats = p.get("statistics",{})

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

            print("Saved:",file_path)

    date += timedelta(days=1)

print("NBA update finished")
