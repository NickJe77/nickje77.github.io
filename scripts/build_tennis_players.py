import os
import json
from collections import defaultdict

INPUT_DIR = "docs/data/tennis/matches"
OUTPUT_DIR = "docs/data/tennis/players"

os.makedirs(OUTPUT_DIR, exist_ok=True)

players = defaultdict(lambda: {
    "matches": [],
    "wins": 0,
    "losses": 0
})


def slug(name):
    return name.lower().replace(" ", "-")


for file in os.listdir(INPUT_DIR):
    if not file.endswith(".json"):
        continue

    data = json.load(open(os.path.join(INPUT_DIR, file)))

    for match in data:
        p1 = match["player1"]
        p2 = match["player2"]
        winner = match["player1"]  # dataset uses winner first

        # player1
        players[p1]["matches"].append(match)
        if winner == p1:
            players[p1]["wins"] += 1
        else:
            players[p1]["losses"] += 1

        # player2
        players[p2]["matches"].append(match)
        if winner == p2:
            players[p2]["wins"] += 1
        else:
            players[p2]["losses"] += 1


index = []

for name, data in players.items():
    s = slug(name)

    data["name"] = name
    data["total_matches"] = len(data["matches"])

    json.dump(
        data,
        open(f"{OUTPUT_DIR}/{s}.json", "w"),
        indent=2
    )

    index.append(name)


json.dump(
    sorted(index),
    open(f"{OUTPUT_DIR}/index.json", "w"),
    indent=2
)

print("Players built:", len(players))
