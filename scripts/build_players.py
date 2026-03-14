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

print("Building NBA player files...")

for season_dir in DATA.iterdir():

    if not season_dir.is_dir():
        continue

    for game_file in season_dir.glob("*.json"):

        if game_file.name in ["index.json", "games.json"]:
            continue

        try:
            game = json.loads(game_file.read_text())
        except:
            continue

        if not isinstance(game, dict):
            continue

        home = game.get("home_team")
        away = game.get("away_team")

        for p in game.get("players", []):

            name = p.get("player_name") or p.get("name") or p.get("player")

            if not name:
                continue

            key = slug(name)

            if key not in players:
                players[key] = {
                    "name": name,
                    "teams": {},
                    "games": []
                }

            team = p.get("team")

            if not team:
                continue

            opp = away if team == home else home

            pts = p.get("points", 0)
            reb = p.get("rebounds", 0)
            ast = p.get("assists", 0)
            stl = p.get("steals", 0)
            blk = p.get("blocks", 0)

            # minutes field can vary in feeds
            mins = p.get("min") or p.get("minutes") or p.get("mp") or 0

            # convert MM:SS to decimal
            if isinstance(mins, str) and ":" in mins:
                try:
                    m, s = mins.split(":")
                    mins = int(m) + int(s) / 60
                except:
                    mins = 0
            elif isinstance(mins, str):
                try:
                    mins = float(mins)
                except:
                    mins = 0

            # Add game log
            players[key]["games"].append({
                "season": game.get("season"),
                "game_id": game.get("game_id"),
                "date": game.get("date"),
                "team": team,
                "opp": opp,
                "minutes": mins,
                "pts": pts,
                "reb": reb,
                "ast": ast,
                "stl": stl,
                "blk": blk
            })

            # Team totals
            if team not in players[key]["teams"]:
                players[key]["teams"][team] = {
                    "games": 0,
                    "minutes": 0,
                    "pts": 0,
                    "reb": 0,
                    "ast": 0,
                    "stl": 0,
                    "blk": 0
                }

            t = players[key]["teams"][team]

            t["games"] += 1
            t["minutes"] += mins
            t["pts"] += pts
            t["reb"] += reb
            t["ast"] += ast
            t["stl"] += stl
            t["blk"] += blk


print("Writing player files...")

index = []

for key, data in players.items():

    file = OUT / f"{key}.json"
    file.write_text(json.dumps(data, indent=2))

    index.append({
        "name": data["name"],
        "slug": key
    })

(OUT / "index.json").write_text(json.dumps(index, indent=2))

print("NBA player database built successfully")
