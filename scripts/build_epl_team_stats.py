import os
import json
from collections import defaultdict

PLAYERS_DIR = "docs/data/epl/players"
OUTPUT_FILE = "docs/data/epl/team_stats.json"

team_data = {}

def to_int(v):
    try:
        return int(float(v or 0))
    except Exception:
        return 0

def ensure_team(team):
    if team not in team_data:
        team_data[team] = {
            "top_scorers": defaultdict(int),
            "yellow_cards": defaultdict(int),
            "red_cards": defaultdict(int),
        }

print("STARTING EPL TEAM STATS BUILD")
print("Looking in:", PLAYERS_DIR)

if not os.path.isdir(PLAYERS_DIR):
    raise SystemExit(f"ERROR: folder not found: {PLAYERS_DIR}")

files = sorted(f for f in os.listdir(PLAYERS_DIR) if f.endswith(".json"))
print("Player files found:", len(files))

checked = 0
matches_seen = 0
stats_seen = 0

for filename in files:
    path = os.path.join(PLAYERS_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            player_json = json.load(f)
    except Exception as e:
        print("BAD JSON:", filename, e)
        continue

    checked += 1

    player_name = str(
        player_json.get("player")
        or player_json.get("name")
        or player_json.get("player_name")
        or ""
    ).strip()

    if not player_name:
        player_name = filename.replace(".json", "").replace("-", " ").title()

    matches = player_json.get("matches")

    if not isinstance(matches, list):
        continue

    for match in matches:
        if not isinstance(match, dict):
            continue

        matches_seen += 1

        team = str(match.get("team") or "").strip()
        if not team:
            continue

        goals = to_int(match.get("goals"))
        yellow = to_int(match.get("yellow_cards"))
        red = to_int(match.get("red_cards"))

        if goals or yellow or red:
            stats_seen += 1

        ensure_team(team)

        if goals:
            team_data[team]["top_scorers"][player_name] += goals

        if yellow:
            team_data[team]["yellow_cards"][player_name] += yellow

        if red:
            team_data[team]["red_cards"][player_name] += red

print("Player JSONs checked:", checked)
print("Matches seen:", matches_seen)
print("Stat rows seen:", stats_seen)
print("Teams found:", len(team_data))

final_output = []

for team in sorted(team_data):
    data = team_data[team]

    scorers = sorted(data["top_scorers"].items(), key=lambda x: x[1], reverse=True)
    yellows = sorted(data["yellow_cards"].items(), key=lambda x: x[1], reverse=True)
    reds = sorted(data["red_cards"].items(), key=lambda x: x[1], reverse=True)

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
        ],
    })

if not final_output:
    raise SystemExit("ERROR: built zero teams. Refusing to overwrite team_stats.json.")

if stats_seen == 0:
    raise SystemExit("ERROR: found player files but zero goals/cards. Refusing to overwrite team_stats.json.")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print("SUCCESS:", OUTPUT_FILE)
print("Teams written:", len(final_output))
print("First team sample:")
print(json.dumps(final_output[0], indent=2, ensure_ascii=False))
