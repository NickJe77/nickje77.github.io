import json
from pathlib import Path
import re

print("BATHURST DRIVER BUILDER")

BASE = Path("docs/data/bathurst")
SEASONS = BASE / "seasons"
DRIVERS = BASE / "drivers"

DRIVERS.mkdir(parents=True, exist_ok=True)

def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

players = {}

for file in SEASONS.glob("*.json"):
    with open(file) as f:
        data = json.load(f)

    year = data["year"]

    for r in data["results"]:
        for d in r["drivers"]:
            s = slug(d)

            if s not in players:
                players[s] = {
                    "name": d,
                    "wins": 0,
                    "races": 0,
                    "results": []
                }

            players[s]["races"] += 1

            if r["position"] in ["1", "1st"]:
                players[s]["wins"] += 1

            players[s]["results"].append({
                "year": year,
                "position": r["position"]
            })

# save
index = []

for s, data in players.items():
    with open(DRIVERS / f"{s}.json", "w") as f:
        json.dump(data, f, indent=2)

    index.append({"name": data["name"], "slug": s})

with open(DRIVERS / "index.json", "w") as f:
    json.dump(sorted(index, key=lambda x: x["name"]), f, indent=2)

print(f"Built {len(players)} drivers")
