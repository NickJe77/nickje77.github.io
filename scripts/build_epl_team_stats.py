import os
import json
from collections import defaultdict

PLAYERS_DIR = "docs/data/epl/players"
OUTPUT_FILE = "docs/data/epl/team_stats.json"

print("RUNNING EPL TEAM STATS BUILDER")

team_data = {}

def ensure_team(team):
    if team not in team_data:
        team_data[team] = {
            "team": team,
            "top_scorers": defaultdict(int),
            "yellow_cards": defaultdict(int),
            "red_cards": defaultdict(int)
        }

def to_int(v):
    try:
        return int(float(v or 0))
    except Exception:
        return 0

def clean(v):
    return str(v or "").strip()

seen = set()

player_files = sorted(
    f for f in os.listdir(PLAYERS_DIR)
    if f.endswith(".json")
)

print(f"Player files found: {len(player_files)}")

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
        player_name = filename.replace(".json", "").replace("-", " ").title()

    matches = player_data.get("matches", [])

    if not isinstance(matches, list):
        continue

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

        opponent = clean(
            match.get("opponent")
            or match.get("opp")
            or match.get("against")
        )

        date = clean(
            match.get("date")
            or match.get("match_date")
            or match.get("game_date")
        )

        dedupe_key = (
            player_name.lower(),
            team.lower(),
            opponent.lower(),
            date
        )

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)

        ensure_team(team)

        goals = to_int(
            match.get("goals")
            or match.get("goal")
        )

        yellow = to_int(
            match.get("yellow_cards")
            or match.get("yellow")
            or match.get("yc")
        )

        red = to_int(
            match.get("red_cards")
            or match.get("red")
            or match.get("rc")
        )

        # PER MATCH SANITY ONLY

        if goals < 0 or goals > 6:
            goals = 0

        if yellow < 0 or yellow > 2:
            yellow = 0

        if red < 0 or red > 1:
            red = 0

        if goals > 0:
            team_data[team]["top_scorers"][player_name] += goals

        if yellow > 0:
            team_data[team]["yellow_cards"][player_name] += yellow

        if red > 0:
            team_data[team]["red_cards"][player_name] += red

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
                "goals": v
            }
            for p, v in scorers[:10]
        ],

        "yellow_cards": [
            {
                "player": p,
                "yellow": v
            }
            for p, v in yellows[:10]
        ],

        "red_cards": [
            {
                "player": p,
                "red": v
            }
            for p, v in reds[:10]
        ]
    })

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print(f"Built {OUTPUT_FILE}")
print(f"Teams written: {len(final_output)}")
print(f"Unique player-match rows counted: {len(seen)}")
