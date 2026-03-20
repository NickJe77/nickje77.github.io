import json
from pathlib import Path
from collections import defaultdict

print("AFL PLAYER BUILDER — SEASON + MASTER")

SEASON = 2026

INPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
SEASON_OUT = Path(f"docs/data/afl/players_{SEASON}.json")
MASTER_OUT = Path("docs/data/afl/players.json")


# -----------------------------
# LOAD DATA
# -----------------------------
if not INPUT.exists():
    print("❌ Missing input:", INPUT)
    exit()

with open(INPUT) as f:
    games = json.load(f)


# -----------------------------
# BUILD PLAYER STATS
# -----------------------------
players = defaultdict(lambda: {
    "player": "",
    "team": "",
    "games": 0,
    "K": 0, "HB": 0, "D": 0, "M": 0,
    "G": 0, "B": 0, "T": 0, "HO": 0,
    "GA": 0, "I50": 0, "CL": 0, "CG": 0,
    "R50": 0, "FF": 0, "FA": 0,
    "AF": 0, "SC": 0
})

for row in games:

    name = row["player"]

    p = players[name]

    p["player"] = name
    p["team"] = row["played_for"]
    p["games"] += 1

    for stat in [
        "K","HB","D","M","G","B","T","HO","GA",
        "I50","CL","CG","R50","FF","FA","AF","SC"
    ]:
        p[stat] += row.get(stat, 0)


# -----------------------------
# CALCULATE AVERAGES
# -----------------------------
for p in players.values():

    g = p["games"] if p["games"] else 1

    for stat in [
        "K","HB","D","M","G","B","T","HO","GA",
        "I50","CL","CG","R50","FF","FA","AF","SC"
    ]:
        p[f"{stat}_avg"] = round(p[stat] / g, 2)


# -----------------------------
# SAVE SEASON FILE
# -----------------------------
season_list = sorted(players.values(), key=lambda x: x["SC"], reverse=True)

with open(SEASON_OUT, "w") as f:
    json.dump(season_list, f, indent=2)

print("✅ Season players saved:", SEASON_OUT)


# -----------------------------
# UPDATE MASTER FILE
# -----------------------------
master = {}

if MASTER_OUT.exists():
    with open(MASTER_OUT) as f:
        for p in json.load(f):
            master[p["player"]] = p


for p in season_list:

    name = p["player"]

    if name not in master:
        master[name] = p.copy()
    else:
        m = master[name]

        m["games"] += p["games"]

        for stat in [
            "K","HB","D","M","G","B","T","HO","GA",
            "I50","CL","CG","R50","FF","FA","AF","SC"
        ]:
            m[stat] += p[stat]

        # recalc averages
        g = m["games"]
        for stat in [
            "K","HB","D","M","G","B","T","HO","GA",
            "I50","CL","CG","R50","FF","FA","AF","SC"
        ]:
            m[f"{stat}_avg"] = round(m[stat] / g, 2)


master_list = sorted(master.values(), key=lambda x: x["SC"], reverse=True)

with open(MASTER_OUT, "w") as f:
    json.dump(master_list, f, indent=2)

print("✅ Master players updated:", MASTER_OUT)
