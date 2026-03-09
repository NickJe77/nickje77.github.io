import requests
import json
import os
from datetime import datetime, timedelta

START_DATE = datetime(2026,2,16)
TODAY = datetime.utcnow()

OUTPUT_DIR = "docs/data/nba/2026"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("NBA updater starting")

def get_games(date):

    ds = date.strftime("%Y%m%d")

    url = f"https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_{ds}.json"

    r = requests.get(url)

    if r.status_code != 200:
        print("No scoreboard:", ds)
        return []

    data = r.json()

    games = data["scoreboard"]["games"]

    print("Checking",ds,"games:",len(games))

    return games


def get_boxscore(game_id):

    url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

    r = requests.get(url)

    if r.status_code != 200:
        print("Boxscore missing:",game_id)
        return None

    return r.json()


date = START_DATE

while date <= TODAY:

    games = get_games(date)

    for g in games:

        game_id = g["gameId"]

        file_path = f"{OUTPUT_DIR}/{game_id}.json"

        if os.path.exists(file_path):
            continue

        box = get_boxscore(game_id)

        if not box:
            continue

        game = box["game"]

        output = {
            "game_id": game_id,
            "season": 2026,
            "date": game["gameTimeUTC"],
            "home_team": game["homeTeam"]["teamName"],
            "away_team": game["awayTeam"]["teamName"],
            "home_score": game["homeTeam"]["score"],
            "away_score": game["awayTeam"]["score"],
            "arena": game["arena"]["arenaName"],
            "players":[]
        }

        for team in ["homeTeam","awayTeam"]:

            team_name = game[team]["teamName"]

            for p in game[team]["players"]:

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
