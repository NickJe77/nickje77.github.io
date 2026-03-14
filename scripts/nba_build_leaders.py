import json
from pathlib import Path
from collections import defaultdict

SEASONS_DIR = Path("docs/data/nba/seasons")
OUTPUT = Path("docs/data/nba/leaders.json")

leaders = []

def leader(players, stat):
    best_player = None
    best_value = -1

    for name,stats in players.items():
        val = stats.get(stat,0)
        if val > best_value:
            best_value = val
            best_player = name

    return {"player":best_player,"value":best_value}

for file in sorted(SEASONS_DIR.glob("*.json")):

    season = file.stem

    with open(file) as f:
        data = json.load(f)

    players = defaultdict(lambda:{
        "points":0,
        "rebounds":0,
        "assists":0,
        "steals":0,
        "blocks":0,
        "threes":0,
        "ft":0
    })

    for game in data.get("games",[]):

        for p in game.get("players",[]):

            name = p.get("player")

            players[name]["points"] += p.get("points",0)
            players[name]["rebounds"] += p.get("rebounds",0)
            players[name]["assists"] += p.get("assists",0)
            players[name]["steals"] += p.get("steals",0)
            players[name]["blocks"] += p.get("blocks",0)
            players[name]["threes"] += p.get("threes",0)
            players[name]["ft"] += p.get("ft",0)

    leaders.append({
        "season":season,
        "points":leader(players,"points"),
        "rebounds":leader(players,"rebounds"),
        "assists":leader(players,"assists"),
        "steals":leader(players,"steals"),
        "blocks":leader(players,"blocks"),
        "threes":leader(players,"threes"),
        "ft":leader(players,"ft")
    })

leaders.sort(key=lambda x: x["season"], reverse=True)

with open(OUTPUT,"w") as f:
    json.dump(leaders,f,indent=2)

print("leaders.json built successfully")
