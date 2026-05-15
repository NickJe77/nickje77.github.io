import os
import json
import shutil
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"
OUT_DIR = "docs/data/epl"
PLAYERS_DIR = f"{OUT_DIR}/players"

print("REBUILDING EPL FROM MATCH FILES")

# =====================================================
# RESET
# =====================================================

if os.path.exists(PLAYERS_DIR):
    shutil.rmtree(PLAYERS_DIR)

os.makedirs(PLAYERS_DIR, exist_ok=True)

# =====================================================
# HELPERS
# =====================================================

def clean(v):
    return str(v or "").strip()

def slugify(v):
    return (
        clean(v)
        .lower()
        .replace("&", "and")
        .replace(".", "")
        .replace("'", "")
        .replace("/", "-")
        .replace(" ", "-")
    )

# =====================================================
# STORAGE
# =====================================================

players = {}
teams = {}

team_scorers = defaultdict(lambda: defaultdict(int))
team_yellows = defaultdict(lambda: defaultdict(int))
team_reds = defaultdict(lambda: defaultdict(int))

# =====================================================
# LOAD ALL MATCH FILES
# =====================================================

match_files = []

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in files:

        if file.endswith(".json"):

            match_files.append(
                os.path.join(root, file)
            )

print("MATCH FILES FOUND:", len(match_files))

# =====================================================
# PROCESS MATCHES
# =====================================================

for path in sorted(match_files):

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except Exception as e:

        print("FAILED:", path, e)
        continue

    if not isinstance(game, dict):
        continue

    home = clean(game.get("home_team"))
    away = clean(game.get("away_team"))

    if not home or not away:
        continue

    for team in [home, away]:

        if team not in teams:

            teams[team] = {
                "team": team
            }

    # =================================================
    # SCORERS
    # =================================================

    scorers = game.get("scorers", [])

    if scorers:

        print("SCORERS FOUND:", path, len(scorers))

    for scorer in scorers:

        if not isinstance(scorer, dict):
            continue

        player = clean(scorer.get("player"))
        team = clean(scorer.get("team"))

        if not player or not team:
            continue

        slug = slugify(player)

        if slug not in players:

            players[slug] = {
                "player": player,
                "slug": slug,
                "goals": 0,
                "yellow_cards": 0,
                "red_cards": 0
            }

        players[slug]["goals"] += 1

        team_scorers[team][player] += 1

    # =================================================
    # YELLOWS
    # =================================================

    yellows = game.get("yellow_cards", [])

    for yellow in yellows:

        if not isinstance(yellow, dict):
            continue

        player = clean(yellow.get("player"))
        team = clean(yellow.get("team"))

        if not player or not team:
            continue

        slug = slugify(player)

        if slug not in players:

            players[slug] = {
                "player": player,
                "slug": slug,
                "goals": 0,
                "yellow_cards": 0,
                "red_cards": 0
            }

        players[slug]["yellow_cards"] += 1

        team_yellows[team][player] += 1

    # =================================================
    # REDS
    # =================================================

    reds = game.get("red_cards", [])

    for red in reds:

        if not isinstance(red, dict):
            continue

        player = clean(red.get("player"))
        team = clean(red.get("team"))

        if not player or not team:
            continue

        slug = slugify(player)

        if slug not in players:

            players[slug] = {
                "player": player,
                "slug": slug,
                "goals": 0,
                "yellow_cards": 0,
                "red_cards": 0
            }

        players[slug]["red_cards"] += 1

        team_reds[team][player] += 1

# =====================================================
# BUILD TEAM STATS
# =====================================================

team_stats = []

for team in sorted(teams.keys()):

    team_stats.append({

        "team": team,

        "top_scorers": [
            {
                "player": p,
                "goals": g
            }
            for p, g in sorted(
                team_scorers[team].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]
        ],

        "yellow_cards": [
            {
                "player": p,
                "yellow_cards": y
            }
            for p, y in sorted(
                team_yellows[team].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]
        ],

        "red_cards": [
            {
                "player": p,
                "red_cards": r
            }
            for p, r in sorted(
                team_reds[team].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]
        ]
    })

# =====================================================
# SAVE PLAYER FILES
# =====================================================

players_index = []

for slug, pdata in players.items():

    with open(
        f"{PLAYERS_DIR}/{slug}.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            pdata,
            f,
            indent=2,
            ensure_ascii=False
        )

    players_index.append(pdata)

# =====================================================
# SAVE OUTPUTS
# =====================================================

with open(
    f"{OUT_DIR}/players.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        players_index,
        f,
        indent=2,
        ensure_ascii=False
    )

with open(
    f"{OUT_DIR}/team_stats.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        team_stats,
        f,
        indent=2,
        ensure_ascii=False
    )

print("PLAYERS:", len(players))
print("PLAYER FILES:", len(os.listdir(PLAYERS_DIR)))

print("ARSENAL REDS:")
for t in team_stats:
    if t["team"] == "Arsenal":
        print(t["red_cards"][:10])

print("DONE")
