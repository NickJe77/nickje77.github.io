import json
import re
import unicodedata
from pathlib import Path

DATA = Path("docs/data/nba")
OUT = DATA / "players"

OUT.mkdir(exist_ok=True)

players = {}

def slug(name):
    s = unicodedata.normalize("NFD", name)
    s = s.encode("ascii", "ignore").decode("utf-8")
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s

def num(v):
    try:
        return int(v)
    except:
        try:
            return float(v)
        except:
            return 0

print("Building NBA player files...")

# 🔥 FORCE ORDER: newest seasons first
season_dirs = sorted(
    [d for d in DATA.iterdir() if d.is_dir()],
    key=lambda x: x.name,
    reverse=True
)

for season_dir in season_dirs:

    season = season_dir.name

    # 🔥 FORCE ORDER: newest games first
    game_files = sorted(
        [f for f in season_dir.glob("*.json") if f.name not in ["index.json","games.json"]],
        key=lambda x: x.name,
        reverse=True
    )

    for game_file in game_files:

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

            pts = num(p.get("points"))
            reb = num(p.get("rebounds"))
            ast = num(p.get("assists"))
            stl = num(p.get("steals"))
            blk = num(p.get("blocks"))

            mins = p.get("min") or p.get("minutes") or p.get("mp") or 0

            if isinstance(mins, str) and ":" in mins:
                try:
                    m, s = mins.split(":")
                    mins = int(m) + int(s) / 60
                except:
                    mins = 0
            else:
                mins = num(mins)

            players[key]["games"].append({
                "season": season,
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

print("Sorting game logs...")

# 🔥 FINAL SORT: newest → oldest (CRITICAL FIX)
for player in players.values():
    player["games"].sort(
        key=lambda g: g.get("date", ""),
        reverse=True
    )

print("Writing player files...")

index = []

for key, data in players.items():

    path = OUT / f"{key}.json"

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    index.append({
        "name": data["name"],
        "slug": key
    })

index.sort(key=lambda x: x["name"])

with open(OUT / "index.json", "w") as f:
    json.dump(index, f, indent=2)

print("NBA player database built successfully")
print("Players created:", len(index))
