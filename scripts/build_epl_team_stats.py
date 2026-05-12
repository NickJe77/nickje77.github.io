import os
import json
from collections import defaultdict, Counter

PLAYERS_DIR = "docs/data/epl/players"
OUTPUT_FILE = "docs/data/epl/team_stats.json"

print("RUNNING EPL TEAM STATS BUILDER - PLAYER TOTAL FALLBACK VERSION")

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

    player_total_goals = to_int(player_data.get("goals"))
    player_total_yellow = to_int(player_data.get("yellow_cards"))
    player_total_red = to_int(player_data.get("red_cards"))

    matches = player_data.get("matches", [])

    if not isinstance(matches, list):
        continue

    seen = set()
    team_counter = Counter()

    match_goal_total = 0
    match_yellow_total = 0
    match_red_total = 0

    player_team_stats = defaultdict(lambda: {
        "goals": 0,
        "yellow": 0,
        "red": 0
    })

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
        team_counter[team] += 1

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

        if goals < 0 or goals > 6:
            goals = 0

        if yellow < 0 or yellow > 2:
            yellow = 0

        if red < 0 or red > 1:
            red = 0

        player_team_stats[team]["goals"] += goals
        player_team_stats[team]["yellow"] += yellow
        player_team_stats[team]["red"] += red

        match_goal_total += goals
        match_yellow_total += yellow
        match_red_total += red

    if not team_counter:
        continue

    primary_team = team_counter.most_common(1)[0][0]

    if player_total_goals > match_goal_total:
        player_team_stats[primary_team]["goals"] += player_total_goals - match_goal_total

    if player_total_yellow > match_yellow_total:
        player_team_stats[primary_team]["yellow"] += player_total_yellow - match_yellow_total

    if player_total_red > match_red_total:
        player_team_stats[primary_team]["red"] += player_total_red - match_red_total

    for team, stats in player_team_stats.items():
        ensure_team(team)

        if stats["goals"] > 0:
            team_data[team]["top_scorers"][player_name] += stats["goals"]

        if stats["yellow"] > 0:
            team_data[team]["yellow_cards"][player_name] += stats["yellow"]

        if stats["red"] > 0:
            team_data[team]["red_cards"][player_name] += stats["red"]

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
            {"player": p, "goals": v}
            for p, v in scorers[:10]
        ],
        "yellow_cards": [
            {"player": p, "yellow": v}
            for p, v in yellows[:10]
        ],
        "red_cards": [
            {"player": p, "red": v}
            for p, v in reds[:10]
        ]
    })

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print(f"Built {OUTPUT_FILE}")
print(f"Teams written: {len(final_output)}")
