import os
import json
from collections import defaultdict

BASE_DIR = "docs/data/epl"
OUTPUT_FILE = "docs/data/epl/team_stats.json"

print("RUNNING EPL TEAM STATS BUILDER - MATCH DATA SOURCE VERSION")

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

def add_goal(team, player, goals=1):
    team = clean(team)
    player = clean(player)
    goals = to_int(goals)
    if not team or not player or goals <= 0:
        return
    ensure_team(team)
    team_data[team]["top_scorers"][player] += goals

def add_yellow(team, player, cards=1):
    team = clean(team)
    player = clean(player)
    cards = to_int(cards)
    if not team or not player or cards <= 0:
        return
    ensure_team(team)
    team_data[team]["yellow_cards"][player] += cards

def add_red(team, player, cards=1):
    team = clean(team)
    player = clean(player)
    cards = to_int(cards)
    if not team or not player or cards <= 0:
        return
    ensure_team(team)
    team_data[team]["red_cards"][player] += cards

def get_team_names(match):
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

    if isinstance(match.get("teams"), dict):
        home = home or clean(match["teams"].get("home"))
        away = away or clean(match["teams"].get("away"))

    return home, away

def normalise_team(raw_team, home, away):
    t = clean(raw_team)

    if not t:
        return ""

    low = t.lower()

    if low in ["home", "h", "team1"]:
        return home

    if low in ["away", "a", "team2"]:
        return away

    return t

def handle_scorers(match):
    home, away = get_team_names(match)

    scorer_keys = [
        "scorers",
        "goals",
        "goal_scorers",
        "events",
        "incidents",
    ]

    for key in scorer_keys:
        items = match.get(key)

        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            event_type = clean(
                item.get("type")
                or item.get("event")
                or item.get("kind")
            ).lower()

            if key in ["events", "incidents"]:
                if "goal" not in event_type and event_type not in ["g"]:
                    continue

                if "own" in event_type:
                    continue

            player = clean(
                item.get("player")
                or item.get("scorer")
                or item.get("name")
                or item.get("player_name")
            )

            team = normalise_team(
                item.get("team")
                or item.get("club")
                or item.get("side"),
                home,
                away
            )

            if not player or not team:
                continue

            add_goal(team, player, 1)

def handle_cards(match):
    home, away = get_team_names(match)

    card_keys = [
        "cards",
        "bookings",
        "events",
        "incidents",
    ]

    for key in card_keys:
        items = match.get(key)

        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            player = clean(
                item.get("player")
                or item.get("name")
                or item.get("player_name")
            )

            team = normalise_team(
                item.get("team")
                or item.get("club")
                or item.get("side"),
                home,
                away
            )

            if not player or not team:
                continue

            card = clean(
                item.get("card")
                or item.get("type")
                or item.get("event")
                or item.get("kind")
            ).lower()

            if "yellow" in card or card in ["yc", "y"]:
                add_yellow(team, player, 1)

            elif "red" in card or card in ["rc", "r"]:
                add_red(team, player, 1)

def handle_player_stats(match):
    home, away = get_team_names(match)

    possible_keys = [
        "players",
        "player_stats",
        "lineups",
        "stats",
    ]

    for key in possible_keys:
        block = match.get(key)

        if isinstance(block, list):
            for p in block:
                if not isinstance(p, dict):
                    continue

                player = clean(
                    p.get("player")
                    or p.get("name")
                    or p.get("player_name")
                )

                team = normalise_team(
                    p.get("team")
                    or p.get("club")
                    or p.get("side"),
                    home,
                    away
                )

                if not player or not team:
                    continue

                add_goal(team, player, p.get("goals") or p.get("goal"))
                add_yellow(team, player, p.get("yellow_cards") or p.get("yellow") or p.get("yc"))
                add_red(team, player, p.get("red_cards") or p.get("red") or p.get("rc"))

        elif isinstance(block, dict):
            for side_key, players in block.items():
                team = normalise_team(side_key, home, away)

                if not isinstance(players, list):
                    continue

                for p in players:
                    if not isinstance(p, dict):
                        continue

                    player = clean(
                        p.get("player")
                        or p.get("name")
                        or p.get("player_name")
                    )

                    if not player or not team:
                        continue

                    add_goal(team, player, p.get("goals") or p.get("goal"))
                    add_yellow(team, player, p.get("yellow_cards") or p.get("yellow") or p.get("yc"))
                    add_red(team, player, p.get("red_cards") or p.get("red") or p.get("rc"))

def process_match(match):
    if not isinstance(match, dict):
        return

    home, away = get_team_names(match)

    if home:
        ensure_team(home)

    if away:
        ensure_team(away)

    handle_scorers(match)
    handle_cards(match)
    handle_player_stats(match)

def process_json_file(path):
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
        if isinstance(data.get("matches"), list):
            for match in data["matches"]:
                process_match(match)
                count += 1

        elif isinstance(data.get("games"), list):
            for match in data["games"]:
                process_match(match)
                count += 1

        elif isinstance(data.get("fixtures"), list):
            for match in data["fixtures"]:
                process_match(match)
                count += 1

        else:
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

        json_files.append(os.path.join(root, file))

json_files = sorted(json_files)

print(f"JSON files found: {len(json_files)}")

total_matches = 0

for path in json_files:
    total_matches += process_json_file(path)

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
            {"player": player, "goals": total}
            for player, total in scorers[:10]
        ],
        "yellow_cards": [
            {"player": player, "yellow": total}
            for player, total in yellows[:10]
        ],
        "red_cards": [
            {"player": player, "red": total}
            for player, total in reds[:10]
        ],
    })

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print(f"Built {OUTPUT_FILE}")
print(f"Teams written: {len(final_output)}")
print(f"Match records scanned: {total_matches}")

for team in final_output:
    if team["team"].lower() == "everton":
        print("Everton top red cards:")
        for p in team["red_cards"]:
            print(p)
        print("Everton top scorers:")
        for p in team["top_scorers"]:
            print(p)
        break
