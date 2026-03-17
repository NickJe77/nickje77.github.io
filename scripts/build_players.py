import json
import re
import unicodedata
from pathlib import Path
from datetime import datetime

DATA = Path("docs/data/nba")
OUT = DATA / "players"

OUT.mkdir(exist_ok=True)

players = {}

# ---------- NORMALISE NAME ----------
def clean_name(name):
    name = str(name or "").strip()
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    name = re.sub(r"\s+", " ", name)
    return name

def slug(name):
    name = clean_name(name).lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")

# ---------- SAFE NUMBER ----------
def num(v):
    try:
        return int(v)
    except:
        try:
            return float(v)
        except:
            return 0

# ---------- DATE ----------
def parse_date(d):
    try:
        return datetime.fromisoformat(str(d).replace("Z",""))
    except:
        return datetime.min

# ---------- FILTER ----------
def is_valid_game(game, team, opp):
    gt = str(game.get("game_type","")).lower()

    if "all" in gt or "star" in gt:
        return False

    bad = {"world","usa","stars","stripes"}
    if str(team).lower() in bad:
        return False
    if str(opp).lower() in bad:
        return False

    return True

print("Building NBA player database...")

# ---------- READ SEASONS ----------
for season_dir in DATA.iterdir():

    if not season_dir.is_dir():
        continue

    season = season_dir.name

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

            raw = p.get("player_name") or p.get("name") or p.get("player")
            if not raw:
                continue

            name = clean_name(raw)
            key = slug(name)

            team = p.get("team")
            if not team:
                continue

            if team != home and team != away:
                if str(team).lower() in str(home).lower():
                    team = home
                elif str(team).lower() in str(away).lower():
                    team = away

            opp = away if team == home else home

            if not is_valid_game(game, team, opp):
                continue

            mins = p.get("min") or p.get("minutes") or p.get("mp") or 0

            if isinstance(mins,str) and ":" in mins:
                try:
                    m,s = mins.split(":")
                    mins = int(m) + int(s)/60
                except:
                    mins = 0
            else:
                mins = num(mins)

            pts = num(p.get("points"))
            reb = num(p.get("rebounds"))
            ast = num(p.get("assists"))
            stl = num(p.get("steals"))
            blk = num(p.get("blocks"))

            # skip only empty rows
            if mins==0 and pts==0 and reb==0 and ast==0 and stl==0 and blk==0:
                continue

            if key not in players:
                players[key] = {
                    "name": name,
                    "games": []
                }

            players[key]["games"].append({
                "season": season,
                "game_id": game.get("game_id"),
                "date": game.get("date"),
                "team": team,
                "opponent": opp,
                "minutes": mins,
                "pts": pts,
                "reb": reb,
                "ast": ast,
                "stl": stl,
                "blk": blk
            })

# ---------- SORT GAMES ----------
print("Sorting games...")

for player in players.values():
    player["games"] = sorted(
        player["games"],
        key=lambda x: parse_date(x.get("date","")),
        reverse=True
    )

# ---------- WRITE FILES ----------
print("Writing player files...")

for f in OUT.glob("*.json"):
    f.unlink()

index = []

for slug_key, data in players.items():

    with open(OUT / f"{slug_key}.json","w") as f:
        json.dump(data,f,indent=2)

    index.append({
        "name": data["name"],
        "slug": slug_key
    })

# ---------- UNIQUE INDEX ----------
unique = {}
for item in index:
    unique[item["slug"]] = item

index = sorted(unique.values(), key=lambda x: x["name"])

with open(OUT / "index.json","w") as f:
    json.dump(index,f,indent=2)

print("DONE")
print("Players:", len(index))
