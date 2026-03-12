import json
import re
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"

OUT.mkdir(exist_ok=True)

players = {}

def slug(name):
    s = name.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s

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

        if not isinstance(game, dict):
            continue

        home = game.get("home_team")
        away = game.get("away_team")

        for p in game.get("players",[]):

            name = p.get("player_name") or p.get("name") or p.get("player")

            if not name:
                continue

            key = slug(name)

            if key not in players:
                players[key] = {
                    "name": name,
                    "games":[]
                }

            team = p.get("team")
            opp = away if team == home else home

            players[key]["games"].append({
                "season": game.get("season"),
                "game_id": game.get("game_id"),
                "date": game.get("date"),
                "team": team,
                "opp": opp,
                "pts": p.get("points",0),
                "reb": p.get("rebounds",0),
                "ast": p.get("assists",0),
                "stl": p.get("steals",0),
                "blk": p.get("blocks",0)
            })


# write player files
index = []

for key,data in players.items():

    file = OUT / f"{key}.json"
    file.write_text(json.dumps(data,indent=2))

    index.append({
        "name": data["name"],
        "slug": key
    })

(OUT / "index.json").write_text(json.dumps(index,indent=2))

print("player files built successfully")
