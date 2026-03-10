import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

FILE = Path("docs/data/nrl/matches/2026.json")

API = "https://site.api.espn.com/apis/site/v2/sports/rugby-league/nrl/scoreboard"

start = datetime(2026,3,1)
today = datetime.utcnow()

# load existing rows
with open(FILE) as f:
    rows = json.load(f)

existing = {r["match_id"] for r in rows}

added = 0
date = start

while date <= today:

    d = date.strftime("%Y%m%d")
    url = f"{API}?dates={d}"

    r = requests.get(url,timeout=30)

    if r.status_code != 200:
        date += timedelta(days=1)
        continue

    data = r.json()

    if "events" not in data:
        date += timedelta(days=1)
        continue

    for g in data["events"]:

        match_id = g["id"]

        if match_id in existing:
            continue

        comp = g["competitions"][0]
        teams = comp["competitors"]

        home = next(t for t in teams if t["homeAway"]=="home")
        away = next(t for t in teams if t["homeAway"]=="away")

        home_team = home["team"]["displayName"]
        away_team = away["team"]["displayName"]

        home_score = int(home.get("score",0))
        away_score = int(away.get("score",0))

        venue = comp.get("venue",{}).get("fullName","")

        row = {
            "season":2026,
            "match_id":match_id,
            "date_iso":g["date"][:10],
            "venue":venue,
            "home_team":home_team,
            "away_team":away_team,
            "home_points":home_score,
            "away_points":away_score,
            "margin":abs(home_score-away_score),
            "total_points":home_score+away_score,
            "player":"",
            "played_for":"",
            "tries":0,
            "goals_made":0,
            "goals_attempted":0,
            "field_goals":0,
            "points":0
        }

        rows.append(row)
        added += 1

    date += timedelta(days=1)

with open(FILE,"w") as f:
    json.dump(rows,f,indent=2)

print("Matches added:",added)
