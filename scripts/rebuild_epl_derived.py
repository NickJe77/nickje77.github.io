import os
import json
import shutil
from collections import defaultdict

SEASONS_DIR = "docs/data/epl/seasons"
OUT_DIR = "docs/data/epl"
PLAYERS_DIR = f"{OUT_DIR}/players"

print("STARTING EPL REBUILD")

# =====================================================
# RESET PLAYERS FOLDER
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

red_seen = set()
yellow_seen = set()

# =====================================================
# LOAD SEASONS
# =====================================================

season_files = sorted([
    os.path.join(SEASONS_DIR, f)
    for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
])

print("SEASON FILES:", len(season_files))

# =====================================================
# PROCESS SEASONS
# =====================================================

for path in season_files:

    print("PROCESSING:", path)

    try:

        with open(path, "r", encoding="utf-8") as f:
            season_json = json.load(f)

    except Exception as e:

        print("FAILED:", e)
        continue

    # SUPPORT BOTH STRUCTURES

    if isinstance(season_json, dict):

        games = season_json.get("games", [])

    elif isinstance(season_json, list):

        games = season_json

    else:

        continue

    # =================================================
    # PROCESS GAMES
    # =================================================

    for game in games:

        if not isinstance(game, dict):
            continue

        match_id = clean(
            game.get("match_id")
            or game.get("id")
        )

        home = clean(
            game.get("home")
            or game.get("home_team")
        )

        away = clean(
            game.get("away")
            or game.get("away_team")
        )

        if not home or not away:
            continue

        # =================================================
        # TEAM TOTALS
        # =================================================

        for team in [home, away]:

            if team not in teams:

                teams[team] = {
                    "team": team,
                    "top_scorers": defaultdict(int),
                    "yellow_cards": defaultdict(int),
                    "red_cards": defaultdict(int)
                }

        # =================================================
        # GOALS
        # =================================================

        for scorer in (
            game.get("scorers")
            or game.get("goals")
            or []
        ):

            if not isinstance(scorer, dict):
                continue

            player = clean(scorer.get("player"))
            team = clean(scorer.get("team"))

            if not player:
                continue

            slug = slugify(player)

            if slug not in players:

                players[slug] = {
                    "player": player,
                    "slug": slug,
                    "goals": 0,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "matches": []
                }

            players[slug]["goals"] += 1

            teams[team]["top_scorers"][player] += 1

        # =================================================
        # YELLOWS
        # =================================================

        for yellow in (
            game.get("yellow_cards")
            or game.get("yellows")
            or []
        ):

            if not isinstance(yellow, dict):
                continue

            player = clean(yellow.get("player"))
            team = clean(yellow.get("team"))

            if not player:
                continue

            key = f"{match_id}_{player}_yellow"

            if key in yellow_seen:
                continue

            yellow_seen.add(key)

            slug = slugify(player)

            if slug not in players:

                players[slug] = {
                    "player": player,
                    "slug": slug,
                    "goals": 0,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "matches": []
                }

            players[slug]["yellow_cards"] += 1

            teams[team]["yellow_cards"][player] += 1

        # =================================================
        # REDS
        # =================================================

        for red in (
            game.get("red_cards")
            or game.get("reds")
            or []
        ):

            if not isinstance(red, dict):
                continue

            player = clean(red.get("player"))
            team = clean(red.get("team"))

            if not player:
                continue

            key = f"{match_id}_{player}_red"

            if key in red_seen:
                continue

            red_seen.add(key)

            slug = slugify(player)

            if slug not in players:

                players[slug] = {
                    "player": player,
                    "slug": slug,
                    "goals": 0,
                    "yellow_cards": 0,
                    "red_cards": 0,
                    "matches": []
                }

            # MAX 1 RED PER MATCH
            players[slug]["red_cards"] += 1

            teams[team]["red_cards"][player] += 1

# =====================================================
# WRITE PLAYER FILES
# =====================================================

players_index = []

for slug, pdata in players.items():

    out_path = f"{PLAYERS_DIR}/{slug}.json"

    with open(out_path, "w", encoding="utf-8") as f:

        json.dump(
            pdata,
            f,
            indent=2,
            ensure_ascii=False
        )

    players_index.append({
        "player": pdata["player"],
        "slug": slug,
        "goals": pdata["goals"],
        "yellow_cards": pdata["yellow_cards"],
        "red_cards": pdata["red_cards"]
    })

# =====================================================
# TEAM STATS
# =====================================================

team_stats = []

for team_name, data in teams.items():

    team_stats.append({

        "team": team_name,

        "top_scorers": [
            {
                "player": p,
                "goals": g
            }
            for p, g in sorted(
                data["top_scorers"].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]
        ],

        "yellow_cards": [
            {
                "player": p,
                "yellow_cards": y
            }
            for p, y in sorted(
                data["yellow_cards"].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]
        ],

        "red_cards": [
            {
                "player": p,
                "red_cards": r
            }
            for p, r in sorted(
                data["red_cards"].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]
        ]
    })

# =====================================================
# SAVE MASTER FILES
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

# =====================================================
# DEBUG
# =====================================================

print("PLAYERS:", len(players))
print("PLAYER FILES:", len(os.listdir(PLAYERS_DIR)))

arsenal = next(
    (
        t for t in team_stats
        if t["team"] == "Arsenal"
    ),
    None
)

if arsenal:

    print("ARSENAL REDS:")
    print(arsenal["red_cards"][:10])

print("DONE")
