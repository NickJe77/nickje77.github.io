import os
import json
from collections import defaultdict

SEASONS_DIR = "docs/data/epl/seasons"
PLAYERS_DIR = "docs/data/epl/players"

print("BUILDING EPL PLAYER FILES")

os.makedirs(PLAYERS_DIR, exist_ok=True)

players = {}

def clean(value):
    return str(value or "").strip()

def to_int(value):
    try:
        return int(float(value))
    except:
        return 0

season_files = sorted(
    f for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
)

for season_file in season_files:

    season_path = os.path.join(SEASONS_DIR, season_file)

    print(f"READING {season_file}")

    try:
        with open(season_path, "r", encoding="utf-8") as f:
            games = json.load(f)
    except Exception as e:
        print(f"FAILED: {season_file}")
        print(e)
        continue

    if not isinstance(games, list):
        continue

    for game in games:

        season = clean(game.get("season"))
        match_id = clean(game.get("match_id") or game.get("id"))
        date = clean(game.get("date"))

        home_team = clean(game.get("home_team"))
        away_team = clean(game.get("away_team"))

        # -----------------------------------
        # PLAYER SECTIONS
        # -----------------------------------

        possible_sections = [
            game.get("home_players"),
            game.get("away_players"),
            game.get("players"),
            game.get("player_stats")
        ]

        all_players = []

        for section in possible_sections:

            if isinstance(section, list):
                all_players.extend(section)

            elif isinstance(section, dict):

                for _, vals in section.items():
                    if isinstance(vals, list):
                        all_players.extend(vals)

        for p in all_players:

            if not isinstance(p, dict):
                continue

            player_name = clean(
                p.get("player")
                or p.get("name")
            )

            if not player_name:
                continue

            slug = (
                player_name.lower()
                .replace("'", "")
                .replace(".", "")
                .replace(" ", "-")
            )

            team = clean(
                p.get("team")
            )

            if not team:

                if clean(p.get("side")).lower() == "home":
                    team = home_team
                elif clean(p.get("side")).lower() == "away":
                    team = away_team

            opponent = away_team if team == home_team else home_team

            goals = to_int(
                p.get("goals")
                or p.get("g")
            )

            yellows = to_int(
                p.get("yellow_cards")
                or p.get("yellow")
                or p.get("yc")
            )

            reds = to_int(
                p.get("red_cards")
                or p.get("red")
                or p.get("rc")
            )

            # -----------------------------------
            # FIX IMPOSSIBLE VALUES
            # -----------------------------------

            if yellows < 0:
                yellows = 0

            if yellows > 2:
                yellows = 2

            if reds < 0:
                reds = 0

            if reds > 1:
                reds = 1

            if goals < 0:
                goals = 0

            if goals > 10:
                goals = 10

            if slug not in players:

                players[slug] = {
                    "player": player_name,
                    "slug": slug,
                    "matches": []
                }

            players[slug]["matches"].append({
                "season": season,
                "date": date,
                "team": team,
                "opponent": opponent,
                "goals": goals,
                "yellow_cards": yellows,
                "red_cards": reds,
                "match_id": match_id
            })

# -----------------------------------
# SAVE PLAYER FILES
# -----------------------------------

for slug, data in players.items():

    output_path = os.path.join(
        PLAYERS_DIR,
        f"{slug}.json"
    )

    try:

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        print(f"FAILED TO SAVE {slug}")
        print(e)

print("DONE")
print(f"PLAYERS BUILT: {len(players)}")
