import json
import os
import urllib.request

BASE = "docs/data/tennis/seasons"
OUTPUT = "docs/data/tennis/player_countries.json"

print("🔍 Loading players from seasons...")

players = set()

# -------------------------
# LOAD PLAYERS
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
        if m.get("player1"):
            players.add(m["player1"].strip())
        if m.get("player2"):
            players.add(m["player2"].strip())

print("👥 Players found:", len(players))

# -------------------------
# COUNTRY CODE → NAME MAP
# -------------------------
COUNTRY_NAMES = {
    "USA": "United States",
    "GBR": "United Kingdom",
    "AUS": "Australia",
    "SUI": "Switzerland",
    "SRB": "Serbia",
    "ESP": "Spain",
    "FRA": "France",
    "GER": "Germany",
    "ITA": "Italy",
    "NED": "Netherlands",
    "BEL": "Belgium",
    "SWE": "Sweden",
    "ARG": "Argentina",
    "BRA": "Brazil",
    "CAN": "Canada",
    "JPN": "Japan",
    "KOR": "South Korea",
    "CHN": "China",
    "IND": "India",
    "RSA": "South Africa",
    "NZL": "New Zealand",
    "CRO": "Croatia",
    "CZE": "Czech Republic",
    "POL": "Poland",
    "AUT": "Austria",
    "DEN": "Denmark",
    "NOR": "Norway",
    "FIN": "Finland",
    "HUN": "Hungary",
    "ROU": "Romania",
    "BUL": "Bulgaria",
    "GRE": "Greece",
    "POR": "Portugal",
    "MEX": "Mexico",
    "CHI": "Chile",
    "COL": "Colombia",
    "PER": "Peru",
    "VEN": "Venezuela",
    "URU": "Uruguay",
    "ECU": "Ecuador",
    "TUR": "Turkey",
    "ISR": "Israel",
    "EGY": "Egypt",
    "MAR": "Morocco",
    "ALG": "Algeria",
    "TUN": "Tunisia",
    "KAZ": "Kazakhstan",
    "UKR": "Ukraine",
    "BLR": "Belarus",
    "RUS": "Russia"
}

# -------------------------
# FETCH ATP DATA
# -------------------------
print("🌍 Fetching country dataset...")

url = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_players.csv"

try:
    with urllib.request.urlopen(url) as response:
        csv_data = response.read().decode("utf-8").splitlines()
except:
    print("❌ Failed to fetch dataset")
    csv_data = []

country_map = {}
surname_map = {}

# -------------------------
# BUILD LOOKUP
# -------------------------
for row in csv_data[1:]:

    parts = row.split(",")

    if len(parts) < 6:
        continue

    first = parts[1].strip()
    last = parts[2].strip()
    code = parts[5].strip()

    if not first or not last or not code:
        continue

    country = COUNTRY_NAMES.get(code, code)  # 🔥 convert here

    full = f"{first} {last}".lower()
    country_map[full] = country

    key = f"{first[0].lower()}_{last.lower()}"
    surname_map[key] = country

# -------------------------
# MATCH PLAYERS
# -------------------------
player_country = {}

for p in players:

    key = p.lower()

    if key in country_map:
        player_country[p] = country_map[key]
        continue

    parts = p.split()
    if len(parts) < 2:
        continue

    first = parts[0]
    last = parts[-1]

    if len(first) == 1:
        lookup = f"{first.lower()}_{last.lower()}"
        if lookup in surname_map:
            player_country[p] = surname_map[lookup]
            continue

    lookup = f"{first.lower()} {last.lower()}"
    if lookup in country_map:
        player_country[p] = country_map[lookup]

print("✅ Players mapped:", len(player_country))

# -------------------------
# SAVE
# -------------------------
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(player_country, f, indent=2)

print("💾 Saved:", OUTPUT)
