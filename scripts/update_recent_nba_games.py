#!/usr/bin/env python3

import requests
import json
from pathlib import Path
from datetime import datetime, timedelta

OUT = Path("docs/data/nba/2026.json")

HEADERS = {
    "User-Agent":"Mozilla/5.0",
    "Referer":"https://www.nba.com"
}

START_DATE = datetime(2026,2,16)

def load_existing():

    if not OUT.exists():
        return {"season":2026,"games":[]}

    with open(OUT) as f:
        return json.load(f)

def save(data):

    OUT.parent.mkdir(parents=True,exist_ok=True)

    with open(OUT,"w") as f:
        json.dump(data,f,indent=2)

def fetch_games(date):

    d = date.strftime("%m/%d/%Y")

    url=f"https://stats.nba.com/stats/scoreboardv2?GameDate={d}&LeagueID=00&DayOffset=0"

    r=requests.get(url,headers=HEADERS)

    j=r.json()

    headers=j["resultSets"][0]["headers"]
    rows=j["resultSets"][0]["rowSet"]

    games=[]

    for r in rows:

        g=dict(zip(headers,r))

        games.append(g)

    return games

def fetch_box(game_id):

    url=f"https://stats.nba.com/stats/boxscoretraditionalv2?GameID={game_id}&StartPeriod=0&EndPeriod=0&StartRange=0&EndRange=0&RangeType=0"

    r=requests.get(url,headers=HEADERS)

    j=r.json()

    headers=j["resultSets"][0]["headers"]
    rows=j["resultSets"][0]["rowSet"]

    players=[]

    for r in rows:

        p=dict(zip(headers,r))

        players.append({
            "player_id":p["PLAYER_ID"],
            "team_id":p["TEAM_ID"],
            "minutes":p["MIN"],
            "points":p["PTS"],
            "rebounds":p["REB"],
            "assists":p["AST"],
            "steals":p["STL"],
            "blocks":p["BLK"],
            "turnovers":p["TO"],
            "fgm":p["FGM"],
            "fga":p["FGA"],
            "tpm":p["FG3M"],
            "tpa":p["FG3A"],
            "ftm":p["FTM"],
            "fta":p["FTA"]
        })

    return players

data = load_existing()

existing_ids=set(g["game_id"] for g in data["games"])

today=datetime.utcnow()

d=START_DATE

added=0

while d<=today:

    try:

        games=fetch_games(d)

        for g in games:

            gid=str(g["GAME_ID"])

            if gid in existing_ids:
                continue

            players=fetch_box(gid)

            game={
                "game_id":gid,
                "date":g["GAME_DATE_EST"][:10],
                "game_type":"Regular Season",
                "home_team":g["HOME_TEAM_NAME"],
                "away_team":g["VISITOR_TEAM_NAME"],
                "home_score":g["PTS_HOME"],
                "away_score":g["PTS_AWAY"],
                "arena":g["ARENA_NAME"],
                "players":players
            }

            data["games"].append(game)

            existing_ids.add(gid)

            added+=1

            print("Added game",gid)

    except:
        pass

    d+=timedelta(days=1)

data["games"]=sorted(data["games"],key=lambda x:x["date"])

save(data)

print("New games added:",added)
