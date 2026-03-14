import json
from pathlib import Path

PLAYERS_FILE = Path("docs/data/nba/players.json")
OUTPUT_FILE = Path("docs/data/nba/stat_leaders.json")

MIN_GAMES = 100
TOP_N = 15

with open(PLAYERS_FILE) as f:
    players = json.load(f)

points_tot = []
reb_tot = []
ast_tot = []

points_pg = []
reb_pg = []
ast_pg = []

for name, p in players.items():

    games = p.get("games", 0)
    pts = p.get("points", 0)
    reb = p.get("rebounds", 0)
    ast = p.get("assists", 0)

    if games == 0:
        continue

    points_tot.append({"player": name, "value": pts})
    reb_tot.append({"player": name, "value": reb})
    ast_tot.append({"player": name, "value": ast})

    if games >= MIN_GAMES:
        points_pg.append({"player": name, "value": round(pts/games, 2)})
        reb_pg.append({"player": name, "value": round(reb/games, 2)})
        ast_pg.append({"player": name, "value": round(ast/games, 2)})

points_tot = sorted(points_tot, key=lambda x: x["value"], reverse=True)[:TOP_N]
reb_tot = sorted(reb_tot, key=lambda x: x["value"], reverse=True)[:TOP_N]
ast_tot = sorted(ast_tot, key=lambda x: x["value"], reverse=True)[:TOP_N]

points_pg = sorted(points_pg, key=lambda x: x["value"], reverse=True)[:TOP_N]
reb_pg = sorted(reb_pg, key=lambda x: x["value"], reverse=True)[:TOP_N]
ast_pg = sorted(ast_pg, key=lambda x: x["value"], reverse=True)[:TOP_N]

output = {
    "totals": {
        "points": points_tot,
        "rebounds": reb_tot,
        "assists": ast_tot
    },
    "per_game": {
        "points": points_pg,
        "rebounds": reb_pg,
        "assists": ast_pg
    }
}

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w") as f:
    json.dump(output, f, indent=2)

print("Stat leaders built")
