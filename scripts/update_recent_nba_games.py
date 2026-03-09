import requests
import json
import os
from datetime import datetime, timedelta

START_DATE = datetime(2026, 2, 16)
TODAY = datetime.utcnow()

OUTPUT_DIR = "docs/data/nba/2026"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_games(date):

    ds = date.strftime("%Y%m%d")
    url = f"https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_{ds}.json"

    r = requests.get(url)

    if r.status_code != 200:
        return []

    data = r.json()
    return data["scoreboard"]["games"]


def get_boxscore(game_id):

    url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

    r = requests.get(url)

    if r.status_code != 200:
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

        out = {
            "game_id": game_id,
            "season": 2026,
            "date": game["gameTimeUTC"],
            "home_team": game["homeTeam"]["teamName"],
            "away_team": game["awayTeam"]["teamName"],
            "home_score": game["homeTeam"]["score"],
            "away_score": game["awayTeam"]["score"],
            "arena": game["arena"]["arenaName"],
            "players": []
        }

        for team in ["homeTeam","awayTeam"]:

            for p in game[team]["players"]:

                stats = p.get("statistics",{})

                out["players"].append({
                    "player": p["name"],
                    "team": game[team]["teamName"],
                    "points": stats.get("points",0),
                    "rebounds": stats.get("reboundsTotal",0),
                    "assists": stats.get("assists",0),
                    "minutes": stats.get("minutes","0")
                })

        with open(file_path,"w") as f:
            json.dump(out,f,indent=2)

        print("Saved",game_id)

    date += timedelta(days=1)
