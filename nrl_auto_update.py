import json
import requests
from pathlib import Path

FILE = Path("docs/data/nrl/matches/2026.json")

SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/rugby-league/nrl/scoreboard"

HEADERS = {"User-Agent":"Mozilla/5.0"}

with open(FILE) as f:
    data = json.load(f)

existing = {str(r["match_id"])+r["player"] for r in data}

games = requests.get(SCOREBOARD,headers=HEADERS).json().get("events",[])

added = 0

for game in games:

    match_id = game["id"]

    summary = requests.get(
        f"https://www.nrl.com/match-centre/{match_id}/player-stats",
        headers=HEADERS
    ).text

    if "playerStats" not in summary:
        continue

    comp = game["competitions"][0]

    home = comp["competitors"][0]
    away = comp["competitors"][1]

    home_team = home["team"]["displayName"]
    away_team = away["team"]["displayName"]

    home_score = int(home.get("score",0))
    away_score = int(away.get("score",0))

    venue = comp.get("venue",{}).get("fullName","")
    date = game["date"][:10]

    stats = json.loads(summary.split("playerStats=")[1].split(";")[0])

    for team in stats:

        played_for = team["teamName"]

        for p in team["players"]:

            name = p["fullName"]

            key = str(match_id)+name

            if key in existing:
                continue

            tries = p.get("tries",0)
            goals = p.get("goals",0)
            field = p.get("fieldGoals",0)
            points = p.get("points",0)

            row = {
                "season":2026,
                "match_id":match_id,
                "venue":venue,
                "crowd":None,
                "date_iso":date,
                "home_team":home_team,
                "away_team":away_team,
                "home_points":home_score,
                "away_points":away_score,
                "margin":abs(home_score-away_score),
                "total_points":home_score+away_score,
                "player":name,
                "played_for":played_for,
                "tries":tries,
                "goals_made":goals,
                "goals_attempted":goals,
                "field_goals":field,
                "points":points
            }

            data.append(row)
            added+=1

with open(FILE,"w") as f:
    json.dump(data,f,indent=2)

print("Rows added:",added)
