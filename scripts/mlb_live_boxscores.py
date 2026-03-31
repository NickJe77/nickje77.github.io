import requests
import json
from pathlib import Path
from datetime import datetime

print("BUILDING PLAYER MAP")

BASE = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

OUT = Path("docs/data/baseball/players.json")

players = {}

def get_games():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}&gameType=R,P"
    data = requests.get(url, headers=HEADERS).json()

    games=[]
    for d in data.get("dates",[]):
        for g in d.get("games",[]):
            games.append(g["gamePk"])
    return games

def extract_players(gamePk):
    url = f"{BASE}/game/{gamePk}/feed/live"
    data = requests.get(url, headers=HEADERS).json()

    teams = data.get("liveData",{}).get("boxscore",{}).get("teams",{})

    for side in ["home","away"]:
        for p in teams.get(side,{}).get("players",{}).values():
            pid = str(p["person"]["id"])
            name = p["person"]["fullName"]

            players[pid] = name

games = get_games()

for g in games:
    try:
        extract_players(g)
    except:
        continue

out = [{"player_id":k,"name":v} for k,v in players.items()]

with open(OUT,"w") as f:
    json.dump(out,f,indent=2)

print("Saved players:", len(out))
