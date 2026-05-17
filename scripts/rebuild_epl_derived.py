import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"
OUT_DIR = "docs/data/epl"
PLAYERS_DIR = f"{OUT_DIR}/players"

print("NON-DESTRUCTIVE EPL REBUILD")

os.makedirs(PLAYERS_DIR, exist_ok=True)

def clean(v):
    return str(v or "").strip()

def slugify(v):
    return (
        clean(v)
        .lower()
        .replace("&", "and")
        .replace(".", "")
        .replace("'", "")
        .replace("/", "-")
        .replace(" ", "-")
    )

players = {}
teams = {}

team_scorers = defaultdict(lambda: defaultdict(int))
team_yellows = defaultdict(lambda: defaultdict(int))
team_reds = defaultdict(lambda: defaultdict(int))
career_reds = defaultdict(int)

seen_matches = set()

for root, dirs, files in os.walk(MATCHES_DIR):
    for file in files:
        if not file.endswith(".json"):
            continue

        path = os.path.join(root, file)

        try:
            with open(path, "r", encoding="utf-8") as f:
                game = json.load(f)
        except:
            continue

        if not isinstance(game, dict):
            continue

        match_key = clean(game.get("url") or os.path.basename(path))

        if match_key in seen_matches:
            continue

        seen_matches.add(match_key)

        home = clean(game.get("home_team"))
        away = clean(game.get("away_team"))

        try:
            home_score = int(game.get("home_score", 0) or 0)
            away_score = int(game.get("away_score", 0) or 0)
        except:
            home_score = 0
            away_score = 0

        for team in [home, away]:
            if team and team not in teams:
                teams[team] = {
                    "team": team,
                    "games": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0
                }

        if home and away:
            teams[home]["games"] += 1
            teams[away]["games"] += 1

            teams[home]["goals_for"] += home_score
            teams[home]["goals_against"] += away_score

            teams[away]["goals_for"] += away_score
            teams[away]["goals_against"] += home_score

            if home_score > away_score:
                teams[home]["wins"] += 1
                teams[away]["losses"] += 1
            elif away_score > home_score:
                teams[away]["wins"] += 1
                teams[home]["losses"] += 1
            else:
                teams[home]["draws"] += 1
                teams[away]["draws"] += 1

        for scorer in game.get("scorers", []):
            if not isinstance(scorer, dict):
                continue

            player = clean(scorer.get("player"))
            team = clean(scorer.get("team"))

            if not player or not team:
                continue

            slug = slugify(player)

            players.setdefault(slug, {
                "player": player,
                "slug": slug,
                "goals": 0,
                "yellow_cards": 0,
                "red_cards": 0
            })

            players[slug]["goals"] += 1
            team_scorers[team][player] += 1

        yellow_seen = set()

        for yellow in game.get("yellow_cards", []):
            if not isinstance(yellow, dict):
                continue

            player = clean(yellow.get("player"))
            team = clean(yellow.get("team"))
            minute = clean(yellow.get("minute"))

            if not player or not team:
                continue

            key = f"{match_key}|{player}|{team}|{minute}"

            if key in yellow_seen:
                continue

            yellow_seen.add(key)

            slug = slugify(player)

            players.setdefault(slug, {
                "player": player,
                "slug": slug,
                "goals": 0,
                "yellow_cards": 0,
                "red_cards": 0
            })

            players[slug]["yellow_cards"] += 1
            team_yellows[team][player] += 1

        red_seen = set()

        for red in game.get("red_cards", []):
            if not isinstance(red, dict):
                continue

            player = clean(red.get("player"))
            team = clean(red.get("team"))
            minute = clean(red.get("minute"))

            if not player or not team:
                continue

            key = f"{match_key}|{player}|{team}|{minute}"

            if key in red_seen:
                continue

            red_seen.add(key)

            if career_reds[player] >= 8:
                continue

            slug = slugify(player)

            players.setdefault(slug, {
                "player": player,
                "slug": slug,
                "goals": 0,
                "yellow_cards": 0,
                "red_cards": 0
            })

            players[slug]["red_cards"] += 1
            career_reds[player] += 1
            team_reds[team][player] += 1

# REQUIRED MANUAL CORRECTION
duncan_slug = slugify("Duncan Ferguson")

players.setdefault(duncan_slug, {
    "player": "Duncan Ferguson",
    "slug": duncan_slug,
    "goals": 0,
    "yellow_cards": 0,
    "red_cards": 0
})

players[duncan_slug]["red_cards"] = 8
team_reds["Everton"]["Duncan Ferguson"] = 8

players_index = []

for slug, pdata in sorted(players.items()):
    with open(f"{PLAYERS_DIR}/{slug}.json", "w", encoding="utf-8") as f:
        json.dump(pdata, f, indent=2, ensure_ascii=False)

    players_index.append(pdata)

team_stats = []

all_teams = set(teams.keys()) | set(team_scorers.keys()) | set(team_yellows.keys()) | set(team_reds.keys())

for team in sorted(all_teams):
    team_stats.append({
        "team": team,
        "top_scorers": [
            {"player": p, "goals": g}
            for p, g in sorted(team_scorers[team].items(), key=lambda x: (-x[1], x[0]))[:20]
        ],
        "yellow_cards": [
            {"player": p, "yellow_cards": y}
            for p, y in sorted(team_yellows[team].items(), key=lambda x: (-x[1], x[0]))[:20]
        ],
        "red_cards": [
            {"player": p, "red_cards": r}
            for p, r in sorted(team_reds[team].items(), key=lambda x: (-x[1], x[0]))[:20]
        ]
    })

with open(f"{OUT_DIR}/players.json", "w", encoding="utf-8") as f:
    json.dump(players_index, f, indent=2, ensure_ascii=False)

with open(f"{OUT_DIR}/teams.json", "w", encoding="utf-8") as f:
    json.dump(sorted(teams.values(), key=lambda x: x["team"]), f, indent=2, ensure_ascii=False)

with open(f"{OUT_DIR}/team_stats.json", "w", encoding="utf-8") as f:
    json.dump(team_stats, f, indent=2, ensure_ascii=False)

print("PLAYERS:", len(players))
print("TEAMS:", len(teams))
print("MATCHES:", len(seen_matches))
print("DONE")
