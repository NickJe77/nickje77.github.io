import json
import os
import requests

BASE = "docs/data/tennis/seasons"
OUTPUT = "docs/data/tennis/player_countries.json"

print("🔍 Loading players from seasons...")

players = set()

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
        if m.get("player1"):
            players.add(m["player1"].strip())
        if m.get("player2"):
            players.add(m["player2"].strip())

print("👥 Players found:", len(players))

# 🔥 LOAD EXTERNAL PLAYER COUNTRY DATA
print("🌍 Fetching country dataset...")

url = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_players.csv"

csv_data = requests.get(url).text.splitlines()

country_map = {}

for row in csv_data[1:]:
    parts = row.split(",")

    if len(parts) < 5:
        continue

    first = parts[1].strip()
    last = parts[2].strip()
    country = parts[4].strip()

    full_name = f"{first} {last}"

    country_map[full_name.lower()] = country

# 🔥 BUILD FINAL MAP
player_country = {}

for p in players:
    key = p.lower()

    if key in country_map:
        player_country[p] = country_map[key]

print("✅ Players mapped:", len(player_country))

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(player_country, f, indent=2)

print("💾 Saved:", OUTPUT)
