import requests
import json
import os

print("Repairing recent NBA games")

BASE_DIR = "docs/data/nba"

START_ID = 22500900   # first broken game


def convert_minutes(raw):

    if not raw:
        return "0:00"

    if isinstance(raw,str) and raw.startswith("PT"):
        try:
            m = raw.replace("PT","").replace("S","").split("M")
            minutes = int(m[0])
            seconds = int(float(m[1]))
            return f"{minutes}:{seconds:02d}"
        except:
            return "0:00"

    return raw


def clean_name(p):

    first = p.get("firstName","")
    last = p.get("familyName","")

    if first or last:
        return f"{first} {last}".strip()

    if p.get("name"):
        return p["name"]

    if p.get("nameI"):
        return p["nameI"]

    return "Unknown"


games_fixed = 0

for season in os.listdir(BASE_DIR):

    season_path = f"{BASE_DIR}/{season}"

    if not os.path.isdir(season_path):
        continue

    for file in os.listdir(season_path):

        if not file.endswith(".json"):
            continue

        if file == "index.json":
            continue

        game_id = file.replace(".json","")

        numeric = int(game_id[2:])

        if numeric < START_ID:
            continue

        box_url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

        r = requests.get(box_url,timeout=30)

        if r.status_code != 200:
            continue

        game = r.json()["game"]

        home = game["homeTeam"]
        away = game["awayTeam"]

        home_team = f'{home.get("teamCity","")} {home.get("teamName","")}'.strip()
        away_team = f'{away.get("teamCity","")} {away.get("teamName","")}'.strip()

        output = {
            "game_id": game_id,
            "date": game.get("gameTimeUTC",""),
            "game_type": "Regular Season",
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home.get("score",0),
            "away_score": away.get("score",0),
            "arena": game.get("arena",{}).get("arenaName",""),
            "players":[]
        }

        for team_key in ["homeTeam","awayTeam"]:

            team = game.get(team_key,{})
            team_name = f'{team.get("teamCity","")} {team.get("teamName","")}'.strip()

            for p in team.get("players",[]):

                stats = p.get("statistics",{})

                output["players"].append({
                    "player": clean_name(p),
                    "team": team_name,
                    "minutes": convert_minutes(stats.get("minutes")),
                    "points": stats.get("points",0),
                    "rebounds": stats.get("reboundsTotal",0),
                    "assists": stats.get("assists",0)
                })

        file_path = f"{season_path}/{file}"

        with open(file_path,"w",encoding="utf-8") as f:
            json.dump(output,f,indent=2)

        games_fixed += 1
        print("Fixed",file_path)

print("Games repaired:",games_fixed)
