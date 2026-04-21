import json
import os

BASE = "docs/data/tennis/seasons"
OUTPUT = "docs/data/tennis/players.json"

players_by_surname = {}

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

        for key in ["player1", "player2"]:

            name = m.get(key)
            if not name:
                continue

            name = name.strip()

            parts = name.split()
            if len(parts) < 2:
                continue

            surname = parts[-1]

            # detect initial vs full name
            is_initial = len(parts[0]) == 1

            if surname not in players_by_surname:
                players_by_surname[surname] = name
            else:
                existing = players_by_surname[surname]

                # if existing is initial but new is full → replace
                if len(existing.split()[0]) == 1 and not is_initial:
                    players_by_surname[surname] = name

# FINAL LIST
players = sorted(set(players_by_surname.values()))

print("👥 Players found:", len(players))

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(players, f, indent=2)

print("✅ Saved to:", OUTPUT)
