import json
from pathlib import Path

DATA = Path("docs/data/nba")

players = {}

for season_dir in DATA.iterdir():

    if not season_dir.is_dir():
        continue

    for game_file in season_dir.glob("*.json"):

        if game_file.name in ["index.json","games.json"]:
            continue

        try:
            game=json.loads(game_file.read_text())
        except:
            continue

        # skip files that are lists
        if not isinstance(game, dict):
            continue

        home=game.get("home_team")
        away=game.get("away_team")

        if not home or not away:
            continue

        for p in game.get("players",[]):

            name=p.get("player_name") or p.get("name") or p.get("player")

            if not name:
                continue

            team=p.get("team")

            if not team:
                continue

            opp = away if team==home else home

            if name not in players:
                players[name]={"games":[]}

            players[name]["games"].append({
                "season":game.get("season"),
                "game_id":game.get("game_id"),
                "date":game.get("date"),
                "team":team,
                "opp":opp,
                "pts":p.get("points",0),
                "reb":p.get("rebounds",0),
                "ast":p.get("assists",0),
                "stl":p.get("steals",0),
                "blk":p.get("blocks",0)
            })

out=DATA/"players.json"

out.write_text(json.dumps(players,indent=2))

print("players.json rebuilt successfully")
