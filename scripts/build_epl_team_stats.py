import os
import json
from collections import defaultdict

PLAYERS_DIR = "docs/data/epl/players"
OUTPUT_FILE = "docs/data/epl/team_stats.json"

print("REBUILDING EPL TEAM STATS")

team_data = {}

def ensure_team(team):
    if team not in team_data:
        team_data[team] = {
            "team": team,
            "top_scorers": defaultdict(int),
            "yellow_cards": defaultdict(int),
            "red_cards": defaultdict(int),
        }

def clean(v):
    return str(v or "").strip()

def to_int(v):
    try:
        return int(float(v))
    except:
        return 0

def is_red_card(card_text):
    text = clean(card_text).lower()

    red_terms = [
        "red",
        "red card",
        "straight red",
        "second yellow red",
        "2nd yellow red"
    ]

    for term in red_terms:
        if term in text:
            return True

    if text == "yellow":
        return False

    return False

processed = set()

player_files = sorted(
    f for f in os.listdir(PLAYERS_DIR)
    if f.endswith(".json")
)

for filename in player_files:

    path = os.path.join(PLAYERS_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            player = json.load(f)
    except Exception:
        continue

    player_name = clean(
        player.get("player") or
        player.get("name")
    )

    if not player_name:
        continue

    matches = player.get("matches", [])

    for match in matches:

        match_id = clean(
            match.get("match_id") or
            match.get("game_id") or
            match.get("id")
        )

        team = clean(
            match.get("team") or
            player.get("team")
        )

        if not team:
            continue

        ensure_team(team)

        # goals
        goals = to_int(
            match.get("goals") or
            match.get("g")
        )

        if goals > 0:
            team_data[team]["top_scorers"][player_name] += goals

        # unique match/player key
        unique_key = f"{player_name}_{match_id}"

        if unique_key in processed:
            continue

        processed.add(unique_key)

        # yellow cards
        yellow = to_int(
            match.get("yellow_cards") or
            match.get("yellow") or
            match.get("yc")
        )

        if yellow > 0:
            team_data[team]["yellow_cards"][player_name] += yellow

        # red cards
        red_total = 0

        # explicit red fields
        explicit_red = to_int(
            match.get("red_cards") or
            match.get("red") or
            match.get("rc")
        )

        red_total += explicit_red

        # card event text
        card_text = clean(
            match.get("card") or
            match.get("card_type")
        )

        if is_red_card(card_text):
            red_total += 1

        if red_total > 0:
            team_data[team]["red_cards"][player_name] += red_total

output = []

for team, data in sorted(team_data.items()):

    scorers = sorted(
        data["top_scorers"].items(),
        key=lambda x: (-x[1], x[0])
    )[:20]

    yellows = sorted(
        data["yellow_cards"].items(),
        key=lambda x: (-x[1], x[0])
    )[:20]

    reds = sorted(
        data["red_cards"].items(),
        key=lambda x: (-x[1], x[0])
    )[:20]

    output.append({
        "team": team,
        "top_scorers": [
            {"player": p, "goals": g}
            for p, g in scorers
        ],
        "yellow_cards": [
            {"player": p, "yellow": y}
            for p, y in yellows
        ],
        "red_cards": [
            {"player": p, "red": r}
            for p, r in reds
        ]
    })

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("DONE")
print(f"Saved: {OUTPUT_FILE}")
