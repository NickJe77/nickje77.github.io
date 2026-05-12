import os
import json
from collections import defaultdict

BASE_DIR = "docs/data/epl"
OUTPUT_FILE = "docs/data/epl/team_stats.json"

print("RUNNING EPL TEAM STATS BUILDER - DIRECT PLAYER STATS VERSION")

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

def add_stat(team, player, goals=0, yellow=0, red=0):

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

def process_player(team, player):

    if not isinstance(player, dict):
        return

    name = clean(
        player.get("player")
        or player.get("name")
        or player.get("player_name")
    )

    if not name:
        return

    goals = (
        player.get("goals")
        or player.get("goal")
        or player.get("gls")
    )

    yellow = (
        player.get("yellow_cards")
        or player.get("yellow")
        or player.get("yc")
        or player.get("bookings")
    )

    red = (
        player.get("red_cards")
        or player.get("red")
        or player.get("rc")
    )

    add_stat(team, name, goals, yellow, red)

def process_match(match):

    if not isinstance(match, dict):
        return

    home = clean(
        match.get("home_team")
        or match.get("home")
        or match.get("homeTeam")
        or match.get("team1")
    )

    away = clean(
        match.get("away_team")
        or match.get("away")
        or match.get("awayTeam")
        or match.get("team2")
    )

    ensure_team(home)
    ensure_team(away)

    # MOST IMPORTANT SECTION
    # handles player_stats.home / away

    player_stats = match.get("player_stats")

    if isinstance(player_stats, dict):

        home_players = (
            player_stats.get("home")
            or player_stats.get(home)
            or []
        )

        away_players = (
            player_stats.get("away")
            or player_stats.get(away)
            or []
        )

        for p in home_players:
            process_player(home, p)

        for p in away_players:
            process_player(away, p)

    # handles lineups.home / away

    lineups = match.get("lineups")

    if isinstance(lineups, dict):

        home_players = (
            lineups.get("home")
            or lineups.get(home)
            or []
        )

        away_players = (
            lineups.get("away")
            or lineups.get(away)
            or []
        )

        for p in home_players:
            process_player(home, p)

        for p in away_players:
            process_player(away, p)

    # handles flat players array

    players = match.get("players")

    if isinstance(players, list):

        for p in players:

            if not isinstance(p, dict):
                continue

            team = clean(
                p.get("team")
                or p.get("club")
                or p.get("side")
            )

            process_player(team, p)

def process_file(path):

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:
        print(f"Skipping {path}: {e}")
        return 0

    count = 0

    if isinstance(data, list):

        for item in data:
            process_match(item)
            count += 1

    elif isinstance(data, dict):

        for key in [
            "matches",
            "games",
            "fixtures"
        ]:

            if isinstance(data.get(key), list):

                for match in data[key]:
                    process_match(match)
                    count += 1

                return count

        process_match(data)
        count += 1

    return count

json_files = []

for root, dirs, files in os.walk(BASE_DIR):

    if "/players" in root.replace("\\", "/"):
        continue

    for file in files:

        if not file.endswith(".json"):
            continue

        if file == "team_stats.json":
            continue

        json_files.append(
            os.path.join(root, file)
        )

json_files = sorted(json_files)

print(f"JSON files found: {len(json_files)}")

total = 0

for path in json_files:
    total += process_file(path)

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

print(f"Built {OUTPUT_FILE}")
print(f"Teams written: {len(final_output)}")
print(f"Matches scanned: {total}")
