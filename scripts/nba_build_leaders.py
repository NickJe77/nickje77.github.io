import json
from pathlib import Path

SEASONS_DIR = Path("docs/data/nba/seasons")
OUT_FILE = Path("docs/data/nba/leaders.json")

leaders = []

def stat(p, names):
    for n in names:
        if n in p:
            return p.get(n,0)
    return 0

for season_file in sorted(SEASONS_DIR.glob("*.json")):

    season = season_file.stem

    try:
        data = json.loads(season_file.read_text())
    except:
        continue

    totals = {}

    for game in data.get("games",[]):

        teams = []

        if "teams" in game:
            teams = game["teams"]

        if "home" in game:
            teams.append(game["home"])

        if "away" in game:
            teams.append(game["away"])

        for team in teams:

            for p in team.get("players",[]):

                name = p.get("name") or p.get("player")

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

                totals[name]["points"] += stat(p,["points","pts"])
                totals[name]["rebounds"] += stat(p,["rebounds","reb","trb"])
                totals[name]["assists"] += stat(p,["assists","ast"])
                totals[name]["steals"] += stat(p,["steals","stl"])
                totals[name]["blocks"] += stat(p,["blocks","blk"])

    if not totals:
        print("No players found in",season)
        continue

    def leader(stat_name):

        player = max(totals, key=lambda x: totals[x][stat_name])

        return {
            "player": player,
            "value": totals[player][stat_name]
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

OUT_FILE.write_text(json.dumps(leaders,indent=2))

print("Leaders built:",len(leaders),"seasons")
