import os
import json
from collections import defaultdict

PLAYERS_DIR = "docs/data/epl/players"
OUTPUT_FILE = "docs/data/epl/team_stats.json"

print("RUNNING EPL TEAM STATS BUILDER - PLAYER FILE VERSION")

team_data = {}

def clean(v):
    return str(v or "").strip()

def to_int(v):
    try:
        return int(float(v or 0))
    except Exception:
        return 0

def ensure_team(team):

    team = clean(team)

    if not team:
        return

    if team not in team_data:
        team_data[team] = {
            "team": team,
            "top_scorers": defaultdict(int),
            "yellow_cards": defaultdict(int),
            "red_cards": defaultdict(int),
        }

def add_stats(team, player, goals=0, yellow=0, red=0):

    team = clean(team)
    player = clean(player)

    if not team or not player:
        return

    ensure_team(team)

    goals = to_int(goals)
    yellow = to_int(yellow)
    red = to_int(red)

    if goals > 0:
        team_data[team]["top_scorers"][player] += goals

    if yellow > 0:
        team_data[team]["yellow_cards"][player] += yellow

    if red > 0:
        team_data[team]["red_cards"][player] += red

player_files = sorted(
    f for f in os.listdir(PLAYERS_DIR)
    if f.endswith(".json")
)

print(f"PLAYER FILES FOUND: {len(player_files)}")

for filename in player_files:

    path = os.path.join(PLAYERS_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            player_data = json.load(f)

    except Exception as e:
        print(f"Skipping {filename}: {e}")
        continue

    player_name = clean(
        player_data.get("player")
        or player_data.get("name")
        or player_data.get("player_name")
    )

    if not player_name:
        player_name = (
            filename
            .replace(".json", "")
            .replace("-", " ")
            .title()
        )

    matches = player_data.get("matches")

    if not isinstance(matches, list):
        continue

    seen = set()

    for match in matches:

        if not isinstance(match, dict):
            continue

        team = clean(
            match.get("team")
            or match.get("club")
            or match.get("squad")
        )

        if not team:
            continue

        # IMPORTANT FIX
        # only dedupe on REAL match ids

        match_id = clean(match.get("match_id"))

        if match_id:

            if match_id in seen:
                continue

            seen.add(match_id)

        goals = (
            match.get("goals")
            or match.get("goal")
            or match.get("gls")
        )

        yellow = (
            match.get("yellow_cards")
            or match.get("yellow")
            or match.get("yc")
            or match.get("bookings")
        )

        red = (
            match.get("red_cards")
            or match.get("red")
            or match.get("rc")
        )

        add_stats(
            team,
            player_name,
            goals,
            yellow,
            red
        )

final_output = []

for team in sorted(team_data):

    data = team_data[team]

    scorers = sorted(
        data["top_scorers"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    yellows = sorted(
        data["yellow_cards"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    reds = sorted(
        data["red_cards"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    final_output.append({
        "team": team,

        "top_scorers": [
            {
                "player": p,
                "goals": g
            }
            for p, g in scorers[:10]
        ],

        "yellow_cards": [
            {
                "player": p,
                "yellow": y
            }
            for p, y in yellows[:10]
        ],

        "red_cards": [
            {
                "player": p,
                "red": r
            }
            for p, r in reds[:10]
        ],
    })

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        final_output,
        f,
        indent=2,
        ensure_ascii=False
    )

print(f"BUILT {OUTPUT_FILE}")
print(f"TEAMS WRITTEN: {len(final_output)}")

for team in final_output:

    if team["team"].lower() == "everton":

        print("\nEVERTON RED CARDS")

        for p in team["red_cards"]:
            print(p)

        print("\nEVERTON GOALS")

        for p in team["top_scorers"]:
            print(p)

        break
