import json
from pathlib import Path

players_dir = Path("docs/data/nba/players")
output_file = Path("docs/data/nba/stat_leaders.json")

TOP = 15
MIN_GAMES = 100

pts_tot=[]
reb_tot=[]
ast_tot=[]
stl_tot=[]
blk_tot=[]
td_tot=[]
qd_tot=[]

pts_pg=[]
reb_pg=[]
ast_pg=[]
stl_pg=[]
blk_pg=[]

pts_p36=[]
reb_p36=[]
ast_p36=[]
stl_p36=[]
blk_p36=[]

print("Building stat leaders...")

for f in players_dir.glob("*.json"):

    try:
        p=json.loads(f.read_text())
    except:
        continue

    name=p.get("name")

    teams=p.get("teams",{})

    g=0
    mins=0
    pts=0
    reb=0
    ast=0
    stl=0
    blk=0
    td=0
    qd=0

    for t in teams.values():

        g+=t.get("games",0)
        mins+=t.get("minutes",0)
        pts+=t.get("pts",0)
        reb+=t.get("reb",0)
        ast+=t.get("ast",0)
        stl+=t.get("stl",0)
        blk+=t.get("blk",0)

    # Detect triple and quadruple doubles
    for game in p.get("games",[]):

        pts_g = game.get("pts",0)
        reb_g = game.get("reb",0)
        ast_g = game.get("ast",0)
        stl_g = game.get("stl",0)
        blk_g = game.get("blk",0)

        categories = 0

        if pts_g >= 10:
            categories += 1
        if reb_g >= 10:
            categories += 1
        if ast_g >= 10:
            categories += 1
        if stl_g >= 10:
            categories += 1
        if blk_g >= 10:
            categories += 1

        if categories >= 3:
            td += 1

        if categories >= 4:
            qd += 1


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

    if qd > 0:
        qd_tot.append({"player":name,"value":qd})


    if g >= MIN_GAMES:

        pts_pg.append({"player":name,"value":round(pts/g,2)})
        reb_pg.append({"player":name,"value":round(reb/g,2)})
        ast_pg.append({"player":name,"value":round(ast/g,2)})
        stl_pg.append({"player":name,"value":round(stl/g,2)})
        blk_pg.append({"player":name,"value":round(blk/g,2)})


    if mins > 0:

        pts_p36.append({"player":name,"value":round((pts/mins)*36,2)})
        reb_p36.append({"player":name,"value":round((reb/mins)*36,2)})
        ast_p36.append({"player":name,"value":round((ast/mins)*36,2)})
        stl_p36.append({"player":name,"value":round((stl/mins)*36,2)})
        blk_p36.append({"player":name,"value":round((blk/mins)*36,2)})


def top(lst):
    return sorted(lst,key=lambda x:x["value"],reverse=True)[:TOP]


output={

"totals":{
"points":top(pts_tot),
"rebounds":top(reb_tot),
"assists":top(ast_tot),
"steals":top(stl_tot),
"blocks":top(blk_tot),
"triple_doubles":top(td_tot),
"quadruple_doubles":top(qd_tot)
},

"per_game":{
"points":top(pts_pg),
"rebounds":top(reb_pg),
"assists":top(ast_pg),
"steals":top(stl_pg),
"blocks":top(blk_pg)
},

"per_36":{
"points":top(pts_p36),
"rebounds":top(reb_p36),
"assists":top(ast_p36),
"steals":top(stl_p36),
"blocks":top(blk_p36)
}

}

output_file.write_text(json.dumps(output,indent=2))

print("Stat leaders created")
