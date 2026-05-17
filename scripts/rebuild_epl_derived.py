import os
import json
import shutil
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"

OUT_DIR = "docs/data/epl"

PLAYERS_DIR = f"{OUT_DIR}/players"

print("SAFE EPL REBUILD")

# =====================================================
# RESET DERIVED ONLY
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

team_scorers = defaultdict(lambda: defaultdict(int))
team_yellows = defaultdict(lambda: defaultdict(int))
team_reds = defaultdict(lambda: defaultdict(int))

seen_matches = set()

# =====================================================
# LOAD MATCH FILES
# =====================================================

match_files = []

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in files:

        if file.endswith(".json"):

            match_files.append(
                os.path.join(root, file)
            )

print("MATCH FILES:", len(match_files))

# =====================================================
# PROCESS
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

    match_key = clean(
        game.get("url")
        or os.path.basename(path)
    )

    if match_key in seen_matches:
        continue

    seen_matches.add(match_key)

    # =================================================
    # SCORERS
    # =================================================

    for scorer in game.get("scorers", []):

        if not isinstance(scorer, dict):
            continue

        player = clean(
            scorer.get("player")
        )

        team = clean(
            scorer.get("team")
        )

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

    seen_yellows = set()

    for yellow in game.get("yellow_cards", []):

        if not isinstance(yellow, dict):
            continue

        player = clean(
            yellow.get("player")
        )

        team = clean(
            yellow.get("team")
        )

        minute = clean(
            yellow.get("minute")
        )

        if not player or not team:
            continue

        key = (
            f"{match_key}|"
            f"{player}|"
            f"{minute}"
        )

        if key in seen_yellows:
            continue

        seen_yellows.add(key)

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

    seen_reds = set()

    for red in game.get("red_cards", []):

        if not isinstance(red, dict):
            continue

        player = clean(
            red.get("player")
        )

        team = clean(
            red.get("team")
        )

        minute_raw = clean(
            red.get("minute")
        )

        if not player or not team:
            continue

        # =============================================
        # FILTER BAD PARSES
        # =============================================

        minute_digits = ""

        for c in minute_raw:

            if c.isdigit():
                minute_digits += c

        try:
            minute = int(minute_digits)
        except:
            minute = 90

        # most false reds are yellows
        if minute < 35:
            continue

        key = (
            f"{match_key}|"
            f"{player}|"
            f"{minute}"
        )

        if key in seen_reds:
            continue

        seen_reds.add(key)

        slug = slugify(player)

        if slug not in players:

            players[slug] = {
                "player": player,
                "slug": slug,
                "goals": 0,
                "yellow_cards": 0,
                "red_cards": 0
            }

        # EPL record ceiling
        if players[slug]["red_cards"] >= 8:
            continue

        players[slug]["red_cards"] += 1

        team_reds[team][player] += 1

# =====================================================
# TEAM STATS
# =====================================================

team_stats = []

all_teams = set()

for t in team_scorers.keys():
    all_teams.add(t)

for t in team_yellows.keys():
    all_teams.add(t)

for t in team_reds.keys():
    all_teams.add(t)

for team in sorted(all_teams):

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
# SAVE PLAYERS
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
# SAVE INDEXES
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
print("MATCHES:", len(seen_matches))
print("DONE")
