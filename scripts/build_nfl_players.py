import os
import json
from collections import defaultdict

GAMES_PATH = "docs/data/nfl/games"
OUTPUT = "docs/data/nfl/players"

os.makedirs(OUTPUT, exist_ok=True)

players = defaultdict(lambda: {
    "games":0,
    "passY":0,
    "passTD":0,
    "rushY":0,
    "rushTD":0,
    "recY":0,
    "recTD":0
})

for file in os.listdir(GAMES_PATH):
    if not file.endswith(".json"):
        continue

    with open(os.path.join(GAMES_PATH, file)) as f:
        data = json.load(f)

    for g in data["games"]:
        for p in g.get("players", []):

            name = p.get("name")
            if not name:
                continue

            players[name]["games"] += 1

            players[name]["passY"] += p.get("passing", {}).get("yards",0)
            players[name]["passTD"] += p.get("passing", {}).get("td",0)

            players[name]["rushY"] += p.get("rushing", {}).get("yards",0)
            players[name]["rushTD"] += p.get("rushing", {}).get("td",0)

            players[name]["recY"] += p.get("receiving", {}).get("yards",0)
            players[name]["recTD"] += p.get("receiving", {}).get("td",0)


# build output
summary = []
index = []

for name, stats in players.items():
    summary.append({
        "name": name,
        **stats
    })
    index.append(name)

summary.sort(key=lambda x: x["name"])
index.sort()

with open(f"{OUTPUT}/summary.json","w") as f:
    json.dump(summary,f,indent=2)

with open(f"{OUTPUT}/index.json","w") as f:
    json.dump(index,f,indent=2)

print("✅ Players built:", len(summary))bui
