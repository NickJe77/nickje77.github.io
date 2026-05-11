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

for filename in os.listdir(PLAYERS_DIR):

    if not filename.endswith(".json"):
        continue

    path = os.path.join(PLAYERS_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            player = json.load(f)

    except Exception:
        continue

    player_name = (
        player.get("player")
        or player.get("name")
        or ""
    ).strip()

    if not player_name:
        continue

    matches = player.get("matches", [])

    for match in matches:

        team = (
            match.get("team")
            or ""
        ).strip()

        if not team:
            continue

        ensure_team(team)

        goals = int(match.get("goals", 0) or 0)
        yellow = int(
            match.get("yellow_cards", 0)
            or match.get("yellow", 0)
            or 0
        )
        red = int(
            match.get("red_cards", 0)
            or match.get("red", 0)
            or 0
        )

        team_data[team]["top_scorers"][player_name] += goals
        team_data[team]["yellow_cards"][player_name] += yellow
        team_data[team]["red_cards"][player_name] += red

final_output = []

for team, data in sorted(team_data.items()):

    scorers = sorted(
        data["top_scorers"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:25]

    yellows = sorted(
        data["yellow_cards"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:25]

    reds = sorted(
        data["red_cards"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:25]

    final_output.append({

        "team": team,

        "top_scorers": [
            {
                "player": p,
                "goals": g
            }
            for p, g in scorers
            if g > 0
        ],

        "yellow_cards": [
            {
                "player": p,
                "yellow": y
            }
            for p, y in yellows
            if y > 0
        ],

        "red_cards": [
            {
                "player": p,
                "red": r
            }
            for p, r in reds
            if r > 0
        ]

    })

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2)

print(f"Built {OUTPUT_FILE}")
