import json
from pathlib import Path

SEASONS_DIR = Path("docs/data/nba/seasons")
OUT_FILE = Path("docs/data/nba/leaders.json")

leaders = []

for file in sorted(SEASONS_DIR.glob("*.json")):

    season = file.stem

    try:
        with open(file) as f:
            data = json.load(f)
    except:
        continue

    totals = {}

    games = data.get("games", [])

    for g in games:

        teams = []

        if "home" in g:
            teams.append(g["home"])

        if "away" in g:
            teams.append(g["away"])

        if "teams" in g:
            teams = g["teams"]

        for team in teams:

            for p in team.get("players", []):

                name = p.get("name")

                if not name:
                    continue

                if name not in totals:
                    totals[name] = {
                        "points":0,
                        "rebounds":0,
                        "assists":0,
                        "steals":0,
                        "blocks":0
                    }

                totals[name]["points"] += p.get("points",0)
                totals[name]["rebounds"] += p.get("rebounds",0)
                totals[name]["assists"] += p.get("assists",0)
                totals[name]["steals"] += p.get("steals",0)
                totals[name]["blocks"] += p.get("blocks",0)

    if not totals:
        continue

    def leader(stat):

        player = max(totals, key=lambda p: totals[p][stat])

        return {
            "player": player,
            "value": totals[player][stat]
        }

    leaders.append({
        "season": season,
        "points": leader("points"),
        "rebounds": leader("rebounds"),
        "assists": leader("assists"),
        "steals": leader("steals"),
        "blocks": leader("blocks")
    })

leaders.sort(key=lambda x: x["season"], reverse=True)

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUT_FILE,"w") as f:
    json.dump(leaders,f,indent=2)

print("leaders.json built with",len(leaders),"seasons")
