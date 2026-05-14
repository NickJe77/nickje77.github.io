import os
import json

MATCHES_DIR = "docs/data/epl/matches"
PLAYERS_DIR = "docs/data/epl/players"

print("BUILDING EPL PLAYERS FROM MATCH FILES")

os.makedirs(PLAYERS_DIR, exist_ok=True)

players = {}

def clean(v):
    return str(v or "").strip()

def to_int(v):
    try:
        return int(float(v))
    except:
        return 0

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
        game.get("match_id") or
        game.get("id")
    )

    season = clean(game.get("season"))
    date = clean(game.get("date"))

    home_team = clean(game.get("home_team"))
    away_team = clean(game.get("away_team"))

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
            p.get("player") or
            p.get("name")
        )

        if not player_name:
            continue

        slug = (
            player_name.lower()
            .replace("'", "")
            .replace(".", "")
            .replace(" ", "-")
        )

        team = clean(p.get("team"))

        if not team:

            side = clean(p.get("side")).lower()

            if side == "home":
                team = home_team
            elif side == "away":
                team = away_team

        opponent = away_team if team == home_team else home_team

        goals = to_int(
            p.get("goals") or
            p.get("g")
        )

        yellows = to_int(
            p.get("yellow_cards") or
            p.get("yellow") or
            p.get("yc")
        )

        reds = to_int(
            p.get("red_cards") or
            p.get("red") or
            p.get("rc")
        )

        # FIX IMPOSSIBLE VALUES

        if yellows < 0:
            yellows = 0

        if yellows > 2:
            yellows = 2

        if reds < 0:
            reds = 0

        if reds > 1:
            reds = 1

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

for slug, data in players.items():

    output_path = os.path.join(
        PLAYERS_DIR,
        f"{slug}.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

print("DONE")
print(f"BUILT {len(players)} PLAYERS")
