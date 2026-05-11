import os
import json
import shutil
from collections import defaultdict

PLAYERS_DIR = "docs/data/epl/players"
OUTPUT_FILE = "docs/data/epl/team_stats.json"
BACKUP_FILE = "docs/data/epl/team_stats.backup.json"

team_data = {}

def ensure_team(team):
    if team not in team_data:
        team_data[team] = {
            "team": team,
            "top_scorers": defaultdict(int),
            "yellow_cards": defaultdict(int),
            "red_cards": defaultdict(int),
        }

def to_int(value):
    try:
        if value is None or value == "":
            return 0
        return int(float(value))
    except Exception:
        return 0

def clean_team(value):
    return str(value or "").strip()

def clean_player(value):
    return str(value or "").strip()

if os.path.exists(OUTPUT_FILE):
    shutil.copyfile(OUTPUT_FILE, BACKUP_FILE)
    print(f"Backup created: {BACKUP_FILE}")

if not os.path.isdir(PLAYERS_DIR):
    raise SystemExit(f"Missing folder: {PLAYERS_DIR}")

for filename in sorted(os.listdir(PLAYERS_DIR)):
    if not filename.endswith(".json"):
        continue

    path = os.path.join(PLAYERS_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            player_file = json.load(f)
    except Exception as e:
        print(f"Skipping {filename}: {e}")
        continue

    player_name = clean_player(
        player_file.get("player")
        or player_file.get("name")
        or player_file.get("player_name")
    )

    if not player_name:
        continue

    matches = player_file.get("matches") or player_file.get("games") or []

    if not isinstance(matches, list):
        continue

    for match in matches:
        if not isinstance(match, dict):
            continue

        team = clean_team(
            match.get("team")
            or match.get("club")
            or match.get("squad")
            or match.get("for")
        )

        if not team:
            continue

        ensure_team(team)

        goals = to_int(
            match.get("goals")
            or match.get("goal")
            or match.get("Gls")
            or match.get("gls")
        )

        yellow = to_int(
            match.get("yellow_cards")
            or match.get("yellow")
            or match.get("yc")
            or match.get("CrdY")
            or match.get("cards_yellow")
        )

        red = to_int(
            match.get("red_cards")
            or match.get("red")
            or match.get("rc")
            or match.get("CrdR")
            or match.get("cards_red")
        )

        if goals > 0:
            team_data[team]["top_scorers"][player_name] += goals

        if yellow > 0:
            team_data[team]["yellow_cards"][player_name] += yellow

        if red > 0:
            team_data[team]["red_cards"][player_name] += red

final_output = []

for team in sorted(team_data):
    data = team_data[team]

    final_output.append({
        "team": team,
        "top_scorers": [
            {"player": player, "goals": total}
            for player, total in sorted(data["top_scorers"].items(), key=lambda x: x[1], reverse=True)
        ][:10],
        "yellow_cards": [
            {"player": player, "yellow": total}
            for player, total in sorted(data["yellow_cards"].items(), key=lambda x: x[1], reverse=True)
        ][:10],
        "red_cards": [
            {"player": player, "red": total}
            for player, total in sorted(data["red_cards"].items(), key=lambda x: x[1], reverse=True)
        ][:10],
    })

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print(f"Fixed {OUTPUT_FILE}")
print(f"Teams built: {len(final_output)}")

for team in final_output[:5]:
    print(
        team["team"],
        "scorers:", len(team["top_scorers"]),
        "yellow:", len(team["yellow_cards"]),
        "red:", len(team["red_cards"])
    )
