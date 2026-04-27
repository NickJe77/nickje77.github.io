import os
import json
from collections import defaultdict

GAMES_PATH = "docs/data/nfl/games"
OUTPUT_PATH = "docs/data/nfl/players"

os.makedirs(OUTPUT_PATH, exist_ok=True)

players = defaultdict(lambda: {
    "games": 0,
    "passY": 0,
    "passTD": 0,
    "rushY": 0,
    "rushTD": 0,
    "recY": 0,
    "recTD": 0
})

for file in os.listdir(GAMES_PATH):
    if not file.endswith(".json"):
        continue

    path = os.path.join(GAMES_PATH, file)

    try:
        with open(path) as f:
            data = json.load(f)
    except:
        continue

    for game in data.get("games", []):
        for p in game.get("players", []):

            name = p.get("name")
            if not name:
                continue

            players[name]["games"] += 1

            passing = p.get("passing", {})
            rushing = p.get("rushing", {})
            receiving = p.get("receiving", {})

            players[name]["passY"] += passing.get("yards", 0)
            players[name]["passTD"] += passing.get("td", 0)

            players[name]["rushY"] += rushing.get("yards", 0)
            players[name]["rushTD"] += rushing.get("td", 0)

            players[name]["recY"] += receiving.get("yards", 0)
            players[name]["recTD"] += receiving.get("td", 0)

summary = []
index = []

for name, stats in players.items():
    summary.append({
        "name": name,
        "games": stats["games"],
        "passY": stats["passY"],
        "passTD": stats["passTD"],
        "rushY": stats["rushY"],
        "rushTD": stats["rushTD"],
        "recY": stats["recY"],
        "recTD": stats["recTD"]
    })
    index.append(name)

summary.sort(key=lambda x: x["name"])
index.sort()

with open(os.path.join(OUTPUT_PATH, "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

with open(os.path.join(OUTPUT_PATH, "index.json"), "w") as f:
    json.dump(index, f, indent=2)

print("Players built:", len(summary))
