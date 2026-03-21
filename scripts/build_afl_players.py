import json
from pathlib import Path
from collections import defaultdict

print("AFL PLAYER BUILDER — CLEAN + CORRECT")

SEASON = 2026

INPUT = Path(f"docs/data/afl/afl_{SEASON}.json")
SEASON_OUT = Path(f"docs/data/afl/players_{SEASON}.json")
MASTER_OUT = Path("docs/data/afl/players.json")

STATS = [
    "K","HB","D","M","G","B","T","HO","GA",
    "I50","CL","CG","R50","FF","FA","AF","SC"
]


# -----------------------------
# LOAD DATA
# -----------------------------
with open(INPUT) as f:
    games = json.load(f)


# -----------------------------
# FILTER VALID PLAYER ROWS
# -----------------------------
def valid_player(row):
    name = row.get("player", "").strip()

    if not name:
        return False

    # ❌ remove junk rows
    if "Match Statistics" in name:
        return False

    if len(name) < 3:
        return False

    return True


# -----------------------------
# BUILD PLAYERS (KEY = player+team)
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

    key = f"{name}__{team}"   # 🔥 prevents cross-team mix

    p = players[key]

    p["player"] = name
    p["team"] = team
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
# SORT + SAVE SEASON
# -----------------------------
season_list = sorted(players.values(), key=lambda x: x["SC"], reverse=True)

with open(SEASON_OUT, "w") as f:
    json.dump(season_list, f, indent=2)

print("✅ Season players built:", len(season_list))


# -----------------------------
# REBUILD MASTER CLEANLY
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


# averages
for m in master.values():

    g = m["games"]

    for stat in STATS:
        m[f"{stat}_avg"] = round(m[stat] / g, 2)


master_list = sorted(master.values(), key=lambda x: x["SC"], reverse=True)

with open(MASTER_OUT, "w") as f:
    json.dump(master_list, f, indent=2)

print("✅ Master players built:", len(master_list))
