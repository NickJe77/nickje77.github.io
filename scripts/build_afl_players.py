import json
from pathlib import Path
from collections import defaultdict

print("AFL PLAYER BUILDER — CLEAN VERSION")

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
    raise FileNotFoundError(f"Missing {INPUT}")

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

    name = row["player"]  # strict — must exist

    p = players[name]

    p["player"] = name
    p["team"] = row["played_for"]
    p["games"] += 1

    for stat in STATS:
        p[stat] += int(row.get(stat, 0))


# -----------------------------
# CALCULATE AVERAGES
# -----------------------------
for p in players.values():

    g = p["games"]

    for stat in STATS:
        p[f"{stat}_avg"] = round(p[stat] / g, 2)


# -----------------------------
# SORT SEASON
# -----------------------------
season_list = sorted(players.values(), key=lambda x: x["SC"], reverse=True)


# -----------------------------
# SAVE SEASON FILE
# -----------------------------
with open(SEASON_OUT, "w") as f:
    json.dump(season_list, f, indent=2)

print("✅ Season players built")


# -----------------------------
# BUILD MASTER (CLEAN REBUILD)
# -----------------------------
# 🔥 NO MERGING — CLEAN STRUCTURE
master = {}

if MASTER_OUT.exists():
    with open(MASTER_OUT) as f:
        existing = json.load(f)

        for p in existing:
            name = p["player"]
            master[name] = p


for p in season_list:

    name = p["player"]

    if name not in master:
        master[name] = p.copy()
        continue

    m = master[name]

    m["games"] += p["games"]

    for stat in STATS:
        m[stat] += p[stat]

    g = m["games"]

    for stat in STATS:
        m[f"{stat}_avg"] = round(m[stat] / g, 2)


# -----------------------------
# SORT MASTER
# -----------------------------
master_list = sorted(master.values(), key=lambda x: x["SC"], reverse=True)


# -----------------------------
# SAVE MASTER FILE
# -----------------------------
with open(MASTER_OUT, "w") as f:
    json.dump(master_list, f, indent=2)

print("✅ Master players built")
