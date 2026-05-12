import os
import json
from collections import defaultdict

PLAYERS_DIR = "docs/data/epl/players"
OUTPUT_FILE = "docs/data/epl/team_stats.json"

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

seen_matches = set()

player_files = [
    f for f in os.listdir(PLAYERS_DIR)
    if f.endswith(".json")
]

print(f"Player files found: {len(player_files)}")

for filename in sorted(player_files):

    path = os.path.join(PLAYERS_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {filename}: {e}")
        continue

    player_name = (
        data.get("player")
        or data.get("name")
        or ""
    ).strip()

    if not player_name:
        continue

    matches = data.get("matches", [])

    if not isinstance(matches, list):
        continue

    for match in matches:

        if not isinstance(match, dict):
            continue

        team = str(match.get("team") or "").strip()

        if not team:
            continue

        match_id = str(
            match.get("match_id")
            or match.get("game_id")
            or match.get("id")
            or ""
        ).strip()

        goals = to_int(match.get("goals"))
        yellow = to_int(match.get("yellow_cards"))
        red = to_int(match.get("red_cards"))

        dedupe_key = (
            player_name,
            team,
            match_id,
            goals,
            yellow,
            red
        )

        if dedupe_key in seen_matches:
            continue

        seen_matches.add(dedupe_key)

        ensure_team(team)

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
                "player": player,
                "goals": total
            }
            for player, total in scorers[:10]
        ],

        "yellow_cards": [
            {
                "player": player,
                "yellow": total
            }
            for player, total in yellows[:10]
        ],

        "red_cards": [
            {
                "player": player,
                "red": total
            }
            for player, total in reds[:10]
        ]
    })

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print(f"Built {OUTPUT_FILE}")
print(f"Teams: {len(final_output)}")
print(f"Unique match records counted: {len(seen_matches)}")
