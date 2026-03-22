import json
import re
import unicodedata
import shutil
from pathlib import Path

print("RUNNING PLAYER BUILDER")

DATA_DIR = Path("docs/data/afl")
OUT = Path("docs/data/afl/players")
INDEX = Path("docs/data/afl/players.json")

if OUT.exists():
    shutil.rmtree(OUT)

OUT.mkdir(parents=True, exist_ok=True)

if INDEX.exists():
    INDEX.unlink()

rows = []

for file in DATA_DIR.glob("afl_*.json"):
    with open(file) as f:
        rows.extend(json.load(f))

players = {}

def clean(name):
    name = unicodedata.normalize("NFD", name)
    return name.encode("ascii", "ignore").decode().strip()

def slug(name):
    return re.sub(r"\s+", "-", clean(name).lower())

for r in rows:

    name = clean(r["player"])
    key = slug(name)

    if key not in players:
        players[key] = {"player": name, "games": [], "seen": set()}

    gid = f"{r['season']}_{r['round']}_{r['played_for']}_{r['played_against']}_{name}"

    if gid in players[key]["seen"]:
        continue

    players[key]["seen"].add(gid)

    players[key]["games"].append({
        "season": r["season"],
        "round": r["round"],
        "team": r["played_for"],
        "opponent": r["played_against"]
    })

index = []

for key, p in players.items():
    p.pop("seen", None)

    with open(OUT / f"{key}.json", "w") as f:
        json.dump(p, f, indent=2)

    index.append({"player": p["player"], "slug": key})

with open(INDEX, "w") as f:
    json.dump(sorted(index, key=lambda x: x["player"]), f, indent=2)

print("DONE PLAYERS")
