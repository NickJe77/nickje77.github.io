import json
from pathlib import Path

players_dir = Path("docs/data/nba/players")
output_file = Path("docs/data/nba/team-leaders.json")

leaders = {}

for file in players_dir.glob("*.json"):

    with open(file) as f:
        player = json.load(f)

    name = player.get("name")

    teams = player.get("teams",{})

    for team,stats in teams.items():

        if team not in leaders:
            leaders[team] = {
                "pts":{"player":"","value":0},
                "reb":{"player":"","value":0},
                "ast":{"player":"","value":0},
                "stl":{"player":"","value":0},
                "blk":{"player":"","value":0}
            }

        if stats.get("pts",0) > leaders[team]["pts"]["value"]:
            leaders[team]["pts"]={"player":name,"value":stats["pts"]}

        if stats.get("reb",0) > leaders[team]["reb"]["value"]:
            leaders[team]["reb"]={"player":name,"value":stats["reb"]}

        if stats.get("ast",0) > leaders[team]["ast"]["value"]:
            leaders[team]["ast"]={"player":name,"value":stats["ast"]}

        if stats.get("stl",0) > leaders[team]["stl"]["value"]:
            leaders[team]["stl"]={"player":name,"value":stats["stl"]}

        if stats.get("blk",0) > leaders[team]["blk"]["value"]:
            leaders[team]["blk"]={"player":name,"value":stats["blk"]}

with open(output_file,"w") as f:
    json.dump(leaders,f,indent=2)

print("Team leaders file created.")
