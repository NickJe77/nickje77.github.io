import json
import os
import requests

BASE = "docs/data/tennis/seasons"
OUTPUT = "docs/data/tennis/player_countries.json"

print("🔍 Loading players from seasons...")

players = set()

# -------------------------
# LOAD PLAYERS FROM YOUR DATA
# -------------------------
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

        if p1 and isinstance(p1, str):
            players.add(p1.strip())

        if p2 and isinstance(p2, str):
            players.add(p2.strip())

print("👥 Players found:", len(players))

# -------------------------
# LOAD ATP DATASET
# -------------------------
print("🌍 Fetching country dataset...")

url = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_players.csv"

try:
    csv_data = requests.get(url, timeout=20).text.splitlines()
except:
    print("❌ Failed to fetch dataset")
    csv_data = []

country_map = {}
surname_map = {}

for row in csv_data[1:]:

    parts = row.split(",")

    if len(parts) < 5:
        continue

    first = parts[1].strip()
    last = parts[2].strip()
    country = parts[4].strip()

    # skip bad rows
    if not first or not last or not country:
        continue

    full_name = f"{first} {last}".lower()
    country_map[full_name] = country

    # initial mapping (R Federer → Roger Federer)
    if len(first) > 0:
        key = f"{first[0].lower()}_{last.lower()}"
        surname_map[key] = country

# -------------------------
# MATCH PLAYERS
# -------------------------
player_country = {}

for p in players:

    if not p or not isinstance(p, str):
        continue

    key = p.lower().strip()

    # ✅ DIRECT MATCH
    if key in country_map:
        player_country[p] = country_map[key]
        continue

    parts = p.split()

    if len(parts) < 2:
        continue

    first = parts[0]
    last = parts[-1]

    if not first or not last:
        continue

    # ✅ INITIAL MATCH (R Federer)
    if len(first) == 1:
        lookup = f"{first.lower()}_{last.lower()}"
        if lookup in surname_map:
            player_country[p] = surname_map[lookup]
            continue

    # ✅ TRY FIRST NAME MATCH (Roger Federer style mismatch)
    lookup_full = f"{first.lower()} {last.lower()}"
    if lookup_full in country_map:
        player_country[p] = country_map[lookup_full]
        continue

print("✅ Players mapped:", len(player_country))

# -------------------------
# SAVE FILE
# -------------------------
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(player_country, f, indent=2)

print("💾 Saved:", OUTPUT)
