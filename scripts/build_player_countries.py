import json
import os

BASE = "docs/data/tennis/seasons"
OUTPUT = "docs/data/tennis/player_countries.json"

player_country = {}

print("🔍 Building player → country map...")

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

        tournament = (m.get("tournament") or "").lower()

        if "davis cup" not in tournament:
            continue

        # 👇 support multiple possible field names
        team1 = m.get("team1") or m.get("country1")
        team2 = m.get("team2") or m.get("country2")

        p1 = m.get("player1")
        p2 = m.get("player2")

        if p1 and team1:
            player_country[p1] = team1

        if p2 and team2:
            player_country[p2] = team2

print("👥 Players mapped:", len(player_country))

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(player_country, f, indent=2)

print("✅ Saved:", OUTPUT)
