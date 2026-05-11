import os
import json
import shutil
from collections import defaultdict

PLAYERS_DIR = "docs/data/epl/players"
OUTPUT_FILE = "docs/data/epl/team_stats.json"
BACKUP_FILE = "docs/data/epl/team_stats.backup.json"
TMP_FILE = "docs/data/epl/team_stats.tmp.json"

team_data = {}

def to_int(v):
    try:
        return int(v)
    except Exception:
        try:
            return int(float(v))
        except Exception:
            return 0

def ensure_team(team):
    if team not in team_data:
        team_data[team] = {
            "team": team,
            "top_scorers": defaultdict(int),
            "yellow_cards": defaultdict(int),
            "red_cards": defaultdict(int),
        }

if not os.path.isdir(PLAYERS_DIR):
    raise SystemExit(f"ERROR: missing folder {PLAYERS_DIR}")

player_files = [f for f in os.listdir(PLAYERS_DIR) if f.endswith(".json")]

print(f"Player files found: {len(player_files)}")

for filename in sorted(player_files):
    path = os.path.join(PLAYERS_DIR, filename)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {filename}: {e}")
        continue

    player_name = str(data.get("player") or data.get("name") or "").strip()
    matches = data.get("matches", [])

    if not player_name or not isinstance(matches, list):
        continue

    for match in matches:
        if not isinstance(match, dict):
            continue

        team = str(match.get("team") or "").strip()

        if not team:
            continue

        ensure_team(team)

        goals = to_int(match.get("goals"))
        yellows = to_int(match.get("yellow_cards"))
        reds = to_int(match.get("red_cards"))

        if goals > 0:
            team_data[team]["top_scorers"][player_name] += goals

        if yellows > 0:
            team_data[team]["yellow_cards"][player_name] += yellows

        if reds > 0:
            team_data[team]["red_cards"][player_name] += reds

final_output = []
total_scorers = 0
total_yellows = 0
total_reds = 0

for team in sorted(team_data):
    data = team_data[team]

    scorers = sorted(data["top_scorers"].items(), key=lambda x: x[1], reverse=True)
    yellows = sorted(data["yellow_cards"].items(), key=lambda x: x[1], reverse=True)
    reds = sorted(data["red_cards"].items(), key=lambda x: x[1], reverse=True)

    total_scorers += len(scorers)
    total_yellows += len(yellows)
    total_reds += len(reds)

    final_output.append({
        "team": team,
        "top_scorers": [
            {"player": player, "goals": goals}
            for player, goals in scorers[:10]
        ],
        "yellow_cards": [
            {"player": player, "yellow": yellow}
            for player, yellow in yellows[:10]
        ],
        "red_cards": [
            {"player": player, "red": red}
            for player, red in reds[:10]
        ],
    })

print(f"Teams built: {len(final_output)}")
print(f"Scorers found: {total_scorers}")
print(f"Yellow-card players found: {total_yellows}")
print(f"Red-card players found: {total_reds}")

if len(final_output) == 0:
    raise SystemExit("ERROR: no teams built. Refusing to overwrite team_stats.json.")

if total_scorers == 0 and total_yellows == 0 and total_reds == 0:
    raise SystemExit("ERROR: no stats found. Refusing to overwrite team_stats.json.")

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

if os.path.exists(OUTPUT_FILE):
    shutil.copyfile(OUTPUT_FILE, BACKUP_FILE)
    print(f"Backup saved: {BACKUP_FILE}")

with open(TMP_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

os.replace(TMP_FILE, OUTPUT_FILE)

print(f"SUCCESS: rebuilt {OUTPUT_FILE}")
