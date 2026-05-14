import os
import json
import shutil
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"
PLAYERS_DIR = "docs/data/epl/players"
TEAM_STATS_FILE = "docs/data/epl/team_stats.json"

print("STARTING HARD RESET")

# -------------------------------------------------
# CLEAN
# -------------------------------------------------

def clean(v):
    return str(v or "").strip()

def slugify(name):

    return (
        clean(name)
        .lower()
        .replace(".", "")
        .replace("'", "")
        .replace(" ", "-")
    )

# -------------------------------------------------
# REMOVE OLD PLAYER FILES
# -------------------------------------------------

if os.path.exists(PLAYERS_DIR):

    print("REMOVING OLD PLAYER FILES")

    shutil.rmtree(PLAYERS_DIR)

os.makedirs(PLAYERS_DIR, exist_ok=True)

# -------------------------------------------------
# REMOVE BAD CARD DATA
# -------------------------------------------------

fixed_matches = 0

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in files:

        if not file.endswith(".json"):
            continue

        path = os.path.join(root, file)

        try:

            with open(path, "r", encoding="utf-8") as f:
                game = json.load(f)

        except Exception:
            continue

        # wipe corrupted cards
        game["yellow_cards"] = []
        game["red_cards"] = []

        with open(path, "w", encoding="utf-8") as f:
            json.dump(game, f, indent=2)

        fixed_matches += 1

print(f"FIXED MATCH FILES: {fixed_matches}")

# -------------------------------------------------
# BUILD PLAYER FILES
# -------------------------------------------------

players = {}

def ensure_player(name):

    slug = slugify(name)

    if slug not in players:

        players[slug] = {
            "player": name,
            "slug": slug,
            "matches": {}
        }

    return slug

match_files = []

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in files:

        if file.endswith(".json"):

            match_files.append(
                os.path.join(root, file)
            )

print(f"FOUND MATCHES: {len(match_files)}")

for path in sorted(match_files):

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except Exception:
        continue

    match_id = clean(
        game.get("match_id")
        or os.path.basename(path).replace(".json", "")
    )

    season = clean(
        os.path.basename(os.path.dirname(path))
    )

    home_team = clean(game.get("home_team"))
    away_team = clean(game.get("away_team"))

    scorers = game.get("scorers", [])

    if not isinstance(scorers, list):
        scorers = []

    for scorer in scorers:

        if not isinstance(scorer, dict):
            continue

        player_name = clean(
            scorer.get("player")
        )

        if not player_name:
            continue

        slug = ensure_player(player_name)

        team = clean(
            scorer.get("team")
        )

        opponent = (
            away_team
            if team == home_team
            else home_team
        )

        if match_id not in players[slug]["matches"]:

            players[slug]["matches"][match_id] = {
                "season": season,
                "team": team,
                "opponent": opponent,
                "goals": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "match_id": match_id
            }

        players[slug]["matches"][match_id]["goals"] += 1

print(f"BUILT PLAYERS: {len(players)}")

# -------------------------------------------------
# SAVE PLAYER FILES
# -------------------------------------------------

for slug, data in players.items():

    matches = list(
        data["matches"].values()
    )

    output = {
        "player": data["player"],
        "slug": data["slug"],
        "matches": matches
    }

    output_path = os.path.join(
        PLAYERS_DIR,
        f"{slug}.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

print("PLAYER FILES SAVED")

# -------------------------------------------------
# BUILD TEAM STATS
# -------------------------------------------------

team_data = {}

def ensure_team(team):

    if team not in team_data:

        team_data[team] = {
            "team": team,
            "top_scorers": defaultdict(int),
            "yellow_cards": [],
            "red_cards": []
        }

for slug, player_data in players.items():

    player_name = clean(
        player_data.get("player")
    )

    matches = player_data.get("matches", {})

    # dict safety
    if isinstance(matches, dict):
        matches = list(matches.values())

    if not isinstance(matches, list):
        continue

    for match in matches:

        if not isinstance(match, dict):
            continue

        team = clean(
            match.get("team")
        )

        if not team:
            continue

        ensure_team(team)

        goals = int(
            match.get("goals", 0)
        )

        if goals > 0:

            team_data[team]["top_scorers"][player_name] += goals

# -------------------------------------------------
# SAVE TEAM STATS
# -------------------------------------------------

output = []

for team, data in sorted(team_data.items()):

    scorers = sorted(
        data["top_scorers"].items(),
        key=lambda x: (-x[1], x[0])
    )[:20]

    output.append({

        "team": team,

        "top_scorers": [
            {
                "player": p,
                "goals": g
            }
            for p, g in scorers
        ],

        "yellow_cards": [],

        "red_cards": []

    })

with open(TEAM_STATS_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("TEAM STATS SAVED")
print("DONE")
