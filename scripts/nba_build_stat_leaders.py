import json
from pathlib import Path

PLAYERS_FILE = Path("docs/data/nba/players.json")
OUTPUT_FILE = Path("docs/data/nba/stat_leaders.json")

MIN_GAMES = 100
TOP = 15


with open(PLAYERS_FILE) as f:
    players = json.load(f)


pts_tot = []
reb_tot = []
ast_tot = []
stl_tot = []
blk_tot = []
td_tot = []

pts_pg = []
reb_pg = []
ast_pg = []
stl_pg = []
blk_pg = []


for name, p in players.items():

    games = p.get("games", 0)
    pts = p.get("points", 0)
    reb = p.get("rebounds", 0)
    ast = p.get("assists", 0)
    stl = p.get("steals", 0)
    blk = p.get("blocks", 0)
    td = p.get("triple_doubles", 0)

    if games == 0:
        continue

    # totals
    pts_tot.append({"player": name, "value": pts})
    reb_tot.append({"player": name, "value": reb})
    ast_tot.append({"player": name, "value": ast})
    stl_tot.append({"player": name, "value": stl})
    blk_tot.append({"player": name, "value": blk})
    td_tot.append({"player": name, "value": td})

    # per game
    if games >= MIN_GAMES:

        pts_pg.append({"player": name, "value": round(pts / games, 2)})
        reb_pg.append({"player": name, "value": round(reb / games, 2)})
        ast_pg.append({"player": name, "value": round(ast / games, 2)})
        stl_pg.append({"player": name, "value": round(stl / games, 2)})
        blk_pg.append({"player": name, "value": round(blk / games, 2)})


def top(lst):
    return sorted(lst, key=lambda x: x["value"], reverse=True)[:TOP]


output = {

    "totals": {

        "points": top(pts_tot),
        "rebounds": top(reb_tot),
        "assists": top(ast_tot),
        "steals": top(stl_tot),
        "blocks": top(blk_tot),
        "triple_doubles": top(td_tot)
    },

    "per_game": {

        "points": top(pts_pg),
        "rebounds": top(reb_pg),
        "assists": top(ast_pg),
        "steals": top(stl_pg),
        "blocks": top(blk_pg)
    }

}


OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w") as f:
    json.dump(output, f, indent=2)


print("Created NBA stat leaders")
print("Output:", OUTPUT_FILE)
