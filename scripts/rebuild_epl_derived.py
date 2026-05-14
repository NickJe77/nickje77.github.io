import os
import json
import shutil
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"
OUT_DIR = "docs/data/epl"
PLAYERS_DIR = f"{OUT_DIR}/players"

TMP_DIR = "docs/data/epl_derived_tmp"
TMP_PLAYERS_DIR = f"{TMP_DIR}/players"

print("REBUILDING EPL DERIVED FILES")
print("IGNORING CORRUPTED CARD DATA")

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

def ensure_player(players, name):

    slug = slugify(name)

    if slug not in players:

        players[slug] = {
            "player": name,
            "slug": slug,
            "matches": {}
        }

    return slug

if os.path.exists(TMP_DIR):
    shutil.rmtree(TMP_DIR)

os.makedirs(TMP_PLAYERS_DIR, exist_ok=True)

players = {}

teams = defaultdict(lambda: {
    "team": "",
    "games": 0,
    "wins": 0,
    "draws": 0,
    "losses": 0,
    "goals_for": 0,
    "goals_against": 0
})

match_files = []

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in files:

        if file.endswith(".json"):

            match_files.append(
                os.path.join(root, file)
            )

print(f"FOUND MATCH FILES: {len(match_files)}")

for path in sorted(match_files):

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except Exception:
        continue

    match_id = clean(
        game.get("match_id")
        or os.path.basename(path).replace(".json", "")
    )

    season = clean(
        game.get("season")
        or os.path.basename(os.path.dirname(path))
    )

    date = clean(game.get("date"))

    home = clean(game.get("home_team"))
    away = clean(game.get("away_team"))

    hs = int(game.get("home_score") or 0)
    ass = int(game.get("away_score") or 0)

    if home:

        teams[home]["team"] = home
        teams[home]["games"] += 1
        teams[home]["goals_for"] += hs
        teams[home]["goals_against"] += ass

        if hs > ass:
            teams[home]["wins"] += 1
        elif hs == ass:
            teams[home]["draws"] += 1
        else:
            teams[home]["losses"] += 1

    if away:

        teams[away]["team"] = away
        teams[away]["games"] += 1
        teams[away]["goals_for"] += ass
        teams[away]["goals_against"] += hs

        if ass > hs:
            teams[away]["wins"] += 1
        elif ass == hs:
            teams[away]["draws"] += 1
        else:
            teams[away]["losses"] += 1

    for scorer in game.get("scorers", []) or []:

        if not isinstance(scorer, dict):
            continue

        name = clean(scorer.get("player"))
        team = clean(scorer.get("team"))

        if not name:
            continue

        slug = ensure_player(players, name)

        opponent = away if team == home else home

        if match_id not in players[slug]["matches"]:

            players[slug]["matches"][match_id] = {
                "season": season,
                "date": date,
                "team": team,
                "opponent": opponent,
                "goals": 0,
                "yellow_cards": 0,
                "red_cards": 0,
                "match_id": match_id
            }

        players[slug]["matches"][match_id]["goals"] += 1

player_index = []

team_stats = {}

for slug, pdata in sorted(players.items()):

    matches = list(
        pdata["matches"].values()
    )

    goals = sum(
        int(m.get("goals", 0))
        for m in matches
    )

    output = {
        "player": pdata["player"],
        "slug": slug,
        "goals": goals,
        "yellow_cards": 0,
        "red_cards": 0,
        "matches": matches
    }

    with open(
        f"{TMP_PLAYERS_DIR}/{slug}.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(output, f, indent=2)

    player_index.append({
        "player": pdata["player"],
        "slug": slug,
        "goals": goals,
        "yellow_cards": 0,
        "red_cards": 0,
        "matches": len(matches)
    })

    for m in matches:

        team = clean(m.get("team"))

        if not team:
            continue

        if team not in team_stats:

            team_stats[team] = {
                "team": team,
                "top_scorers": defaultdict(int),
                "yellow_cards": defaultdict(int),
                "red_cards": defaultdict(int)
            }

        team_stats[team]["top_scorers"][pdata["player"]] += int(
            m.get("goals", 0)
        )

teams_out = sorted(
    teams.values(),
    key=lambda x: x["team"]
)

team_stats_out = []

for team, data in sorted(team_stats.items()):

    team_stats_out.append({

        "team": team,

        "top_scorers": [

            {
                "player": p,
                "goals": g
            }

            for p, g in sorted(
                data["top_scorers"].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]

            if g > 0
        ],

        "yellow_cards": [],

        "red_cards": []

    })

with open(
    f"{TMP_DIR}/players.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(player_index, f, indent=2)

with open(
    f"{TMP_DIR}/teams.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(teams_out, f, indent=2)

with open(
    f"{TMP_DIR}/team_stats.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(team_stats_out, f, indent=2)

print(f"PLAYERS BUILT: {len(players)}")
print(f"TEAMS BUILT: {len(teams_out)}")
print(f"TEAM STATS BUILT: {len(team_stats_out)}")

if os.path.exists(PLAYERS_DIR):
    shutil.rmtree(PLAYERS_DIR)

shutil.move(TMP_PLAYERS_DIR, PLAYERS_DIR)

shutil.move(
    f"{TMP_DIR}/players.json",
    f"{OUT_DIR}/players.json"
)

shutil.move(
    f"{TMP_DIR}/teams.json",
    f"{OUT_DIR}/teams.json"
)

shutil.move(
    f"{TMP_DIR}/team_stats.json",
    f"{OUT_DIR}/team_stats.json"
)

shutil.rmtree(TMP_DIR, ignore_errors=True)

print("DONE")
