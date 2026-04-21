import json
import os

BASE = "docs/data/tennis/seasons"
OUTPUT = "docs/data/tennis/players.json"

players = {}
# key = lowercase full name
# value = best version (full name preferred)

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

            clean_key = name.lower()

            is_initial = len(parts[0]) == 1

            if clean_key not in players:
                players[clean_key] = name
            else:
                existing = players[clean_key]
                existing_initial = len(existing.split()[0]) == 1

                # replace initial with full name
                if existing_initial and not is_initial:
                    players[clean_key] = name

# FINAL LIST
final_players = sorted(set(players.values()))

print("👥 Players found:", len(final_players))

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(final_players, f, indent=2)

print("✅ Saved to:", OUTPUT)
