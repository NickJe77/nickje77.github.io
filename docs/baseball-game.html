import requests
import json
from pathlib import Path
from datetime import datetime

print("MLB LIVE BOXSCORE BUILDER (FIXED)")

SEASON = 2026
BASE = "https://statsapi.mlb.com/api/v1"

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_DATE = "2026-03-26"
END_DATE = datetime.utcnow().strftime("%Y-%m-%d")

OUTPUT_DIR = Path(f"docs/data/baseball/boxscores/{SEASON}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TEAM_MAP = {
    108:"LAA",109:"ARI",110:"BAL",111:"BOS",112:"CHN",113:"CIN",
    114:"CLE",115:"COL",116:"DET",117:"HOU",118:"KCA",119:"LAN",
    120:"WAS",121:"NYN",133:"OAK",134:"PIT",135:"SDN",136:"SEA",
    137:"SFN",138:"SLN",139:"TBA",140:"TEX",141:"TOR",142:"MIN",
    143:"PHI",144:"ATL",145:"CHA",146:"MIA",147:"NYA",158:"MIL"
}

def team_code(team):
    return TEAM_MAP.get(team["id"], team.get("abbreviation","UNK"))

# -----------------------------
# GET GAMES
# -----------------------------
def get_games():
    url = f"{BASE}/schedule?sportId=1&startDate={START_DATE}&endDate={END_DATE}&gameType=R,P"
    data = requests.get(url, headers=HEADERS).json()

    games=[]
    for d in data.get("dates",[]):
        for g in d.get("games",[]):
            home=g["teams"]["home"]["team"]
            away=g["teams"]["away"]["team"]

            games.append({
                "gamePk":g["gamePk"],
                "date":g["gameDate"][:10],
                "home":team_code(home),
                "away":team_code(away)
            })

    print("FOUND", len(games), "GAMES")
    return games

# -----------------------------
# BUILD BATTING
# -----------------------------
def build_batting(players):
    rows=[]
    for p in players.values():
        stats=p.get("stats",{}).get("batting",{})
        if not stats:
            continue

        rows.append({
            "player_id":str(p["person"]["id"]),
            "AB":stats.get("atBats",0),
            "R":stats.get("runs",0),
            "H":stats.get("hits",0),
            "RBI":stats.get("rbi",0),
            "BB":stats.get("baseOnBalls",0),
            "SO":stats.get("strikeOuts",0)
        })
    return rows

# -----------------------------
# BUILD PITCHING
# -----------------------------
def build_pitching(players):
    rows=[]
    for p in players.values():
        stats=p.get("stats",{}).get("pitching",{})
        if not stats:
            continue

        rows.append({
            "player_id":str(p["person"]["id"]),
            "IP":stats.get("inningsPitched","0"),
            "H":stats.get("hits",0),
            "R":stats.get("runs",0),
            "ER":stats.get("earnedRuns",0),
            "BB":stats.get("baseOnBalls",0),
            "SO":stats.get("strikeOuts",0)
        })
    return rows

# -----------------------------
# BUILD GAME (FIXED SOURCE)
# -----------------------------
def build_game(g):

    url=f"{BASE}/game/{g['gamePk']}/feed/live"
    data=requests.get(url,headers=HEADERS).json()

    box=data.get("liveData",{}).get("boxscore",{}).get("teams",{})

    if not box:
        print("No boxscore yet:", g["gamePk"])
        return None

    home=box.get("home",{})
    away=box.get("away",{})

    game_id=f"{g['home']}{g['date'].replace('-','')}0"

    return {
        "game_id":game_id,
        "date":g["date"],
        "season":SEASON,
        "home_code":g["home"],
        "away_code":g["away"],
        "home_team":g["home"],
        "away_team":g["away"],

        "batters_home":build_batting(home.get("players",{})),
        "batters_away":build_batting(away.get("players",{})),
        "pitchers_home":build_pitching(home.get("players",{})),
        "pitchers_away":build_pitching(away.get("players",{}))
    }

# -----------------------------
# MAIN
# -----------------------------
print("STARTING BUILD...")

games=get_games()

for g in games:
    try:
        game_data=build_game(g)

        if not game_data:
            continue

        out=OUTPUT_DIR / f"{game_data['game_id']}.json"

        print("WRITING:", out)

        with open(out,"w") as f:
            json.dump(game_data,f,indent=2)

        print("Saved:", game_data["game_id"])

    except Exception as e:
        print("ERROR:", g["gamePk"], e)

print("DONE")
