import json
from pathlib import Path
from collections import defaultdict

print("AFL PLAYER BUILDER — MULTI-SEASON (PRODUCTION)")

DATA_DIR = Path("docs/data/afl")
SEASON = 2026

SEASON_OUT = DATA_DIR / f"players_{SEASON}.json"
MASTER_OUT = DATA_DIR / "players.json"

STATS = [
    "K","HB","D","M","G","B","T","HO","GA",
    "I50","CL","CG","R50","FF","FA","AF","SC"
]


# -----------------------------
# LOAD ALL SEASON FILES
# -----------------------------
files = sorted(DATA_DIR.glob("afl_*.json"))

if not files:
    raise Exception("No AFL files found")

all_games = []
season_games = []

for f in files:

    year = int(f.stem.split("_")[1])

    with open(f) as file:
        data = json.load(file)

        all_games.extend(data)

        if year == SEASON:
            season_games.extend(data)


print(f"Loaded {len(files)} seasons")
print(f"Total games: {len(all_games)}")


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
# BUILD PLAYERS FUNCTION
# -----------------------------
def build_players(games):

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

    # averages
    for p in players.values():
        g = p["games"]
        for stat in STATS:
            p[f"{stat}_avg"] = round(p[stat] / g, 2)

    return list(players.values())


# -----------------------------
# BUILD SEASON
# -----------------------------
season_players = build_players(season_games)

season_players = sorted(season_players, key=lambda x: x["SC"], reverse=True)

with open(SEASON_OUT, "w") as f:
    json.dump(season_players, f, indent=2)

print(f"✅ Season players: {len(season_players)}")


# -----------------------------
# BUILD MASTER (ALL YEARS)
# -----------------------------
career = defaultdict(lambda: {
    "player": "",
    "games": 0,
    **{s: 0 for s in STATS}
})

for p in build_players(all_games):

    name = p["player"]
    m = career[name]

    m["player"] = name
    m["games"] += p["games"]

    for stat in STATS:
        m[stat] += p[stat]


# averages
for m in career.values():
    g = m["games"]
    for stat in STATS:
        m[f"{stat}_avg"] = round(m[stat] / g, 2)


career_list = sorted(career.values(), key=lambda x: x["SC"], reverse=True)

with open(MASTER_OUT, "w") as f:
    json.dump(career_list, f, indent=2)

print(f"✅ Career players: {len(career_list)}")
