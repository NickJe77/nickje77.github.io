import json
import os

BASE = "docs/data/tennis/seasons"
OUTPUT = "docs/data/tennis/players.json"

players = set()

print("🔍 Scanning seasons...")

for file in os.listdir(BASE):

    if not file.endswith(".json"):
        continue

    path = os.path.join(BASE, file)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        continue

    matches = data if isinstance(data, list) else data.get("matches", [])

    for m in matches:

        p1 = m.get("player1")
        p2 = m.get("player2")

        # 🔥 ONLY USE FULL NAME FIELDS
        if p1 and len(p1) > 3:
            players.add(p1.strip())

        if p2 and len(p2) > 3:
            players.add(p2.strip())

print("👥 Players found:", len(players))

players = sorted(players)

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(players, f, indent=2)

print("✅ Saved to:", OUTPUT)
