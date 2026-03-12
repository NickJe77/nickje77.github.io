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
            game = json.loads(game_file.read_text())
        except:
            continue

        for p in game.get("players",[]):

            name = (
                p.get("player_name")
                or p.get("name")
                or p.get("player")
                or ""
            )

            if not name:
                continue

            if name not in players:
                players[name] = {
                    "games":0,
                    "points":0,
                    "rebounds":0,
                    "assists":0,
                    "teams":set()
                }

            rec = players[name]

            rec["games"] += 1
            rec["points"] += p.get("points",0)
            rec["rebounds"] += p.get("rebounds",0)
            rec["assists"] += p.get("assists",0)

            if "team" in p:
                rec["teams"].add(p["team"])

for p in players.values():
    p["teams"] = list(p["teams"])

out = DATA / "players.json"
out.write_text(json.dumps(players,indent=2))

print("players.json built")
