import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"
PLAYERS_DIR = "docs/data/epl/players"

print("BUILDING EPL PLAYER FILES")

os.makedirs(PLAYERS_DIR, exist_ok=True)

players = {}

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

print(f"FOUND {len(match_files)} MATCH FILES")

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

    # -----------------------------------
    # GOALS
    # -----------------------------------

    scorers = game.get("scorers", [])

    for s in scorers:

        if not isinstance(s, dict):
            continue

        player_name = clean(s.get("player"))

        if not player_name:
            continue

        slug = ensure_player(player_name)

        team = clean(s.get("team"))

        opponent = away_team if team == home_team else home_team

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

    # -----------------------------------
    # YELLOWS
    # -----------------------------------

    yellows = game.get("yellow_cards", [])

    for y in yellows:

        if not isinstance(y, dict):
            continue

        player_name = clean(y.get("player"))

        if not player_name:
            continue

        slug = ensure_player(player_name)

        team = clean(y.get("team"))

        opponent = away_team if team == home_team else home_team

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

        if players[slug]["matches"][match_id]["yellow_cards"] < 2:
            players[slug]["matches"][match_id]["yellow_cards"] += 1

    # -----------------------------------
    # REDS
    # -----------------------------------

    reds = game.get("red_cards", [])

    for r in reds:

        if not isinstance(r, dict):
            continue

        player_name = clean(r.get("player"))

        if not player_name:
            continue

        slug = ensure_player(player_name)

        team = clean(r.get("team"))

        opponent = away_team if team == home_team else home_team

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

        # clamp to max 1 red per match
        players[slug]["matches"][match_id]["red_cards"] = 1

# -----------------------------------
# SAVE
# -----------------------------------

for slug, data in players.items():

    matches = list(data["matches"].values())

    matches = sorted(
        matches,
        key=lambda x: x["match_id"]
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

print("DONE")
print(f"BUILT {len(players)} PLAYERS")
