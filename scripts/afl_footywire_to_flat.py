import json
from pathlib import Path
from collections import defaultdict

print("AFL PLAYER BUILDER — SEASON + MASTER (FINAL SAFE)")

SEASON = 2026

INPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
SEASON_OUT = Path(f"docs/data/afl/players_{SEASON}.json")
MASTER_OUT = Path("docs/data/afl/players.json")

STATS = [
    "K","HB","D","M","G","B","T","HO","GA",
    "I50","CL","CG","R50","FF","FA","AF","SC"
]


# -----------------------------
# LOAD MATCH DATA
# -----------------------------
if not INPUT.exists():
    print("❌ Missing input:", INPUT)
    exit()

with open(INPUT) as f:
    games = json.load(f)


# -----------------------------
# BUILD SEASON PLAYERS
# -----------------------------
players = defaultdict(lambda: {
    "player": "",
    "team": "",
    "games": 0,
    **{s: 0 for s in STATS}
})

for row in games:

    name = row.get("player")
    if not name:
        continue

    p = players[name]

    p["player"] = name
    p["team"] = row.get("played_for", "")
    p["games"] += 1

    for stat in STATS:
        p[stat] += row.get(stat, 0)


# -----------------------------
# CALCULATE AVERAGES
# -----------------------------
for p in players.values():

    g = p["games"] if p["games"] else 1

    for stat in STATS:
        p[f"{stat}_avg"] = round(p[stat] / g, 2)


# -----------------------------
# SORT SEASON (SAFE)
# -----------------------------
season_list = sorted(players.values(), key=lambda x: x.get("SC", 0), reverse=True)


# -----------------------------
# SAVE SEASON FILE
# -----------------------------
with open(SEASON_OUT, "w") as f:
    json.dump(season_list, f, indent=2)

print("✅ Season players saved:", SEASON_OUT)


# -----------------------------
# LOAD MASTER FILE (SAFE)
# -----------------------------
master = {}

if MASTER_OUT.exists():
    try:
        with open(MASTER_OUT) as f:
            existing = json.load(f)

            for p in existing:
                name = p.get("player")
                if name:
                    master[name] = p
    except:
        print("⚠️ Master file corrupted — rebuilding fresh")
        master = {}


# -----------------------------
# MERGE SEASON INTO MASTER
# -----------------------------
for p in season_list:

    name = p["player"]

    if name not in master:
        master[name] = p.copy()
        continue

    m = master[name]

    # games
    m["games"] = m.get("games", 0) + p.get("games", 0)

    # stats (SAFE)
    for stat in STATS:
        m[stat] = m.get(stat, 0) + p.get(stat, 0)

    # averages (SAFE)
    g = m.get("games", 1)

    for stat in STATS:
        m[f"{stat}_avg"] = round(m.get(stat, 0) / g, 2)


# -----------------------------
# SORT MASTER (SAFE)
# -----------------------------
master_list = sorted(master.values(), key=lambda x: x.get("SC", 0), reverse=True)


# -----------------------------
# SAVE MASTER FILE
# -----------------------------
with open(MASTER_OUT, "w") as f:
    json.dump(master_list, f, indent=2)

print("✅ Master players updated:", MASTER_OUT)
