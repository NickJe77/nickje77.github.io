import json
from pathlib import Path
from collections import defaultdict

print("AFL PLAYER BUILDER — CLEAN + CORRECT")

SEASON = 2026

# 🔥 FIXED INPUT PATH (MATCH YOUR SCRAPER OUTPUT)
INPUT = Path(f"docs/data/afl/afl_{SEASON}.json")

# If your scraper uses a different name, change ONLY this line

SEASON_OUT = Path(f"docs/data/afl/players_{SEASON}.json")
MASTER_OUT = Path("docs/data/afl/players.json")

STATS = [
    "K","HB","D","M","G","B","T","HO","GA",
    "I50","CL","CG","R50","FF","FA","AF","SC"
]


# -----------------------------
# LOAD DATA
# -----------------------------
if not INPUT.exists():
    raise FileNotFoundError(f"❌ Expected file not found: {INPUT}")

with open(INPUT) as f:
    games = json.load(f)


# -----------------------------
# VALID PLAYER FILTER
# -----------------------------
def valid_player(row):
    name = row.get("player", "").strip()

    if not name:
        return False

    if "Match Statistics" in name:
        return False

    return True


# -----------------------------
# BUILD PLAYERS (TEAM SAFE)
# -----------------------------
players = defaultdict(lambda: {
    "player": "",
    "team": "",
    "games": 0,
    **{s: 0 for s in STATS}
})

for row in games:

    if not valid_player(row):
        continue

    name = row["player"].strip()
    team = row.get("played_for", "").strip()

    if not team:
        continue

    key = f"{name}__{team}"

    p = players[key]

    p["player"] = name
    p["team"] = team
    p["games"] += 1

    for stat in STATS:
        p[stat] += int(row.get(stat, 0))


# -----------------------------
# AVERAGES
# -----------------------------
for p in players.values():

    g = p["games"]

    for stat in STATS:
        p[f"{stat}_avg"] = round(p[stat] / g, 2)


# -----------------------------
# SAVE SEASON
# -----------------------------
season_list = sorted(players.values(), key=lambda x: x["SC"], reverse=True)

with open(SEASON_OUT, "w") as f:
    json.dump(season_list, f, indent=2)

print(f"✅ Season players built: {len(season_list)}")


# -----------------------------
# BUILD MASTER CLEAN
# -----------------------------
master = defaultdict(lambda: {
    "player": "",
    "games": 0,
    **{s: 0 for s in STATS}
})

for p in season_list:

    name = p["player"]
    m = master[name]

    m["player"] = name
    m["games"] += p["games"]

    for stat in STATS:
        m[stat] += p[stat]


for m in master.values():

    g = m["games"]

    for stat in STATS:
        m[f"{stat}_avg"] = round(m[stat] / g, 2)


master_list = sorted(master.values(), key=lambda x: x["SC"], reverse=True)

with open(MASTER_OUT, "w") as f:
    json.dump(master_list, f, indent=2)

print(f"✅ Master players built: {len(master_list)}")
