import json
import requests
from pathlib import Path

FILE = Path("docs/data/nrl/matches/2026.json")

URL = "https://site.api.espn.com/apis/site/v2/sports/rugby-league/nrl/scoreboard"

with open(FILE) as f:
    data = json.load(f)

existing = set()
for r in data:
    existing.add(r["match_id"] + r["player"])

res = requests.get(URL)
games = res.json()["events"]

added = 0

for game in games:

    match_id = game["id"]

    comp = game["competitions"][0]

    home = comp["competitors"][0]
    away = comp["competitors"][1]

    home_team = home["team"]["displayName"]
    away_team = away["team"]["displayName"]

    home_score = int(home.get("score",0))
    away_score = int(away.get("score",0))

    venue = comp["venue"]["fullName"]
    date = game["date"][:10]

    box = requests.get(
        f"https://site.web.api.espn.com/apis/v2/sports/rugby-league/nrl/summary?event={match_id}"
    ).json()

    if "boxscore" not in box:
        continue

    for team in box["boxscore"]["players"]:

        played_for = team["team"]["displayName"]

        for stat_group in team["statistics"]:

            for athlete in stat_group["athletes"]:

                name = athlete["athlete"]["displayName"]

                key = match_id + name

                if key in existing:
                    continue

                stats = athlete["stats"]

                tries = int(stats[0]) if len(stats) > 0 else 0
                goals = int(stats[1]) if len(stats) > 1 else 0
                field = int(stats[2]) if len(stats) > 2 else 0
                points = int(stats[3]) if len(stats) > 3 else 0

                row = {
                    "season": 2026,
                    "match_id": match_id,
                    "venue": venue,
                    "crowd": None,
                    "date_iso": date,
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_points": home_score,
                    "away_points": away_score,
                    "margin": abs(home_score-away_score),
                    "total_points": home_score+away_score,
                    "player": name,
                    "played_for": played_for,
                    "tries": tries,
                    "goals_made": goals,
                    "goals_attempted": goals,
                    "field_goals": field,
                    "points": points
                }

                data.append(row)
                added += 1

with open(FILE,"w") as f:
    json.dump(data,f,indent=2)

print("Rows added:",added)
