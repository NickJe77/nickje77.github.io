import json
from pathlib import Path

players_file = Path("docs/data/nba/players.json")
output_file = Path("docs/data/nba/stat_leaders.json")

MIN_GAMES = 100
TOP = 15

with open(players_file) as f:
    players = json.load(f)

pts_tot=[]
reb_tot=[]
ast_tot=[]
stl_tot=[]
blk_tot=[]
td_tot=[]

pts_pg=[]
reb_pg=[]
ast_pg=[]
stl_pg=[]
blk_pg=[]


for name, p in players.items():

    g = p.get("games",0)
    pts = p.get("points",0)
    reb = p.get("rebounds",0)
    ast = p.get("assists",0)
    stl = p.get("steals",0)
    blk = p.get("blocks",0)
    td  = p.get("triple_doubles",0)

    if g == 0:
        continue


    if pts > 0:
        pts_tot.append({"player":name,"value":pts})

    if reb > 0:
        reb_tot.append({"player":name,"value":reb})

    if ast > 0:
        ast_tot.append({"player":name,"value":ast})

    if stl > 0:
        stl_tot.append({"player":name,"value":stl})

    if blk > 0:
        blk_tot.append({"player":name,"value":blk})

    if td > 0:
        td_tot.append({"player":name,"value":td})


    if g >= MIN_GAMES:

        if pts > 0:
            pts_pg.append({"player":name,"value":round(pts/g,2)})

        if reb > 0:
            reb_pg.append({"player":name,"value":round(reb/g,2)})

        if ast > 0:
            ast_pg.append({"player":name,"value":round(ast/g,2)})

        if stl > 0:
            stl_pg.append({"player":name,"value":round(stl/g,2)})

        if blk > 0:
            blk_pg.append({"player":name,"value":round(blk/g,2)})


def top(lst):
    return sorted(lst, key=lambda x:x["value"], reverse=True)[:TOP]


output = {

    "totals":{
        "points":top(pts_tot),
        "rebounds":top(reb_tot),
        "assists":top(ast_tot),
        "steals":top(stl_tot),
        "blocks":top(blk_tot),
        "triple_doubles":top(td_tot)
    },

    "per_game":{
        "points":top(pts_pg),
        "rebounds":top(reb_pg),
        "assists":top(ast_pg),
        "steals":top(stl_pg),
        "blocks":top(blk_pg)
    }

}


with open(output_file,"w") as f:
    json.dump(output,f,indent=2)

print("Created stat leaders:", output_file)
