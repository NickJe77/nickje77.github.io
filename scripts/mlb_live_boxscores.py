import requests
import json
from pathlib import Path
from datetime import datetime

print("BUILDING PLAYER MAP (SAFE)")

BASE = "https://statsapi.mlb.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

OUT = Path("docs/data/baseball/players.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

players = {}


# -------------------------
# LOAD EXISTING PLAYERS
# -------------------------
if OUT.exists():
    try:
        with open(OUT) as f:
            existing = json.load(f)
            for p in existing:
                players[p["player_id"]] = p["name"]
        print(f"Loaded existing players: {len(players)}")
    except:
        print("Failed to load existing players")


# -------------------------
# GET GAMES
# -------------------------
def get_games():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}&gameType=R,P"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        print("Schedule request failed")
        return []

    data = res.json()

    games = []
    for d in data.get("dates", []):
        for g in d.get("games", []):
            games.append(g["gamePk"])

    return games


# -------------------------
# EXTRACT PLAYERS
# -------------------------
def extract_players(gamePk):
    url = f"{BASE}/game/{gamePk}/feed/live"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        return

    data = res.json()

    teams = data.get("liveData", {}).get("boxscore", {}).get("teams", {})

    for side in ["home", "away"]:
        for p in teams.get(side, {}).get("players", {}).values():
            try:
                pid = str(p["person"]["id"])
                name = p["person"]["fullName"]

                players[pid] = name
            except:
                continue


# -------------------------
# MAIN
# -------------------------
games = get_games()

if not games:
    print("NO GAMES FOUND → NOT TOUCHING FILE")
    exit()

print(f"Processing {len(games)} games")

for g in games:
    try:
        extract_players(g)
    except:
        continue


# -------------------------
# SAVE (ONLY IF DATA EXISTS)
# -------------------------
if not players:
    print("NO PLAYERS FOUND → NOT SAVING")
    exit()

out = [{"player_id": k, "name": v} for k, v in players.items()]

with open(OUT, "w") as f:
    json.dump(out, f, indent=2)

print("Saved players:", len(out))
