import json
import requests
from pathlib import Path

print("NRL UPDATE WITH FULL PLAYER STATS")

SEASON = 2026

BASE = Path("docs/data/nrl")
SEASON_FILE = BASE / "seasons" / f"{SEASON}.json"
INDEX_FILE = BASE / "index.json"

headers = {"User-Agent": "Mozilla/5.0"}

BASE.mkdir(parents=True, exist_ok=True)
SEASON_FILE.parent.mkdir(parents=True, exist_ok=True)

def get_round(round_name):

    url = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}&round={round_name}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return []

    return r.json().get("fixtures", [])

print("Downloading fixtures")

fixtures = []
fixtures += get_round("opening")
fixtures += get_round("all")

print("Fixtures detected:", len(fixtures))

games = []

for m in fixtures:

    home = m["homeTeam"]["nickName"]
    away = m["awayTeam"]["nickName"]

    match_id = m["matchId"]

    round_title = m["roundTitle"]

    if "Opening" in round_title:
        round_num = 1
    else:
        round_num = int(round_title.split()[1])

    kickoff = m["clock"]["kickOffTimeLong"]
    date_iso = kickoff[:10]

    venue = m["venue"]

    home_pts = m.get("homeScore", 0)
    away_pts = m.get("awayScore", 0)

    game = {
        "match_id": match_id,
        "season": SEASON,
        "round": round_num,
        "date_iso": date_iso,
        "venue": venue,
        "home_team": home,
        "away_team": away,
        "home_points": home_pts,
        "away_points": away_pts,
        "players": []
    }

    # PLAYER STATS
    try:

        stats_url = f"https://stats.nrl.com/api/match/{match_id}"

        s = requests.get(stats_url, headers=headers)

        if s.status_code == 200:

            stats = s.json()

            for team in stats["teams"]:

                team_name = team["nickName"]

                for p in team["players"]:

                    game["players"].append({

                        "name": p["fullName"],
                        "team": team_name,
                        "position": p.get("position"),
                        "tries": p.get("tries",0),
                        "tackles": p.get("tackles",0),
                        "run_metres": p.get("runMetres",0),
                        "line_breaks": p.get("lineBreaks",0)

                    })

    except:
        pass

    games.append(game)

games.sort(key=lambda x:(x["round"],x["date_iso"]))

with open(SEASON_FILE,"w") as f:
    json.dump(games,f,indent=2)

print("Season written")

# UPDATE INDEX
if INDEX_FILE.exists():

    with open(INDEX_FILE) as f:
        index=json.load(f)

else:

    index={}

if "seasons" not in index:
    index["seasons"]=[]

if SEASON not in index["seasons"]:
    index["seasons"].append(SEASON)

index["seasons"]=sorted(index["seasons"])

with open(INDEX_FILE,"w") as f:
    json.dump(index,f,indent=2)

print("Index updated")
print("Games written:",len(games))
