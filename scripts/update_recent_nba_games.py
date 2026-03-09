import requests
import json
import os

print("NBA updater starting")

BASE_DIR = "docs/data/nba"
os.makedirs(BASE_DIR, exist_ok=True)

schedule_url = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"

r = requests.get(schedule_url)

if r.status_code != 200:
    print("Schedule download failed")
    exit()

data = r.json()

game_dates = data["leagueSchedule"]["gameDates"]

games_saved = 0

for d in game_dates:

    for g in d["games"]:

        game_id = g["gameId"]

        game_date = g["gameDateEst"]
        year = int(game_date[:4])
        month = int(game_date[5:7])

        if month >= 10:
            season = year + 1
        else:
            season = year

        season_dir = f"{BASE_DIR}/{season}"
        os.makedirs(season_dir, exist_ok=True)

        game_file = f"{season_dir}/{game_id}.json"

        if os.path.exists(game_file):
            continue

        box_url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

        box = requests.get(box_url)

        if box.status_code != 200:
            continue

        game = box.json()["game"]

        prefix = game_id[:3]

        if prefix == "001":
            game_type = "Preseason"
        elif prefix == "002":
            game_type = "Regular Season"
        elif prefix == "004":
            game_type = "Playoffs"
        else:
            game_type = "Other"

        output = {
            "game_id": game_id,
            "date": game["gameTimeUTC"],
            "game_type": game_type,
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

        with open(game_file,"w") as f:
            json.dump(output,f,indent=2)

        index_path = f"{season_dir}/index.json"

        if os.path.exists(index_path):
            with open(index_path) as f:
                index = json.load(f)
        else:
            index = {"games":[]}

        if game_id not in index["games"]:
            index["games"].append(game_id)

        with open(index_path,"w") as f:
            json.dump(index,f,indent=2)

        games_saved += 1
        print("Saved", game_file)

print("Games saved:",games_saved)
print("NBA updater finished")
