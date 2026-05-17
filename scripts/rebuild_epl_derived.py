import os
import json
from collections import defaultdict

MATCHES_DIR = "docs/data/epl/matches"
OUT_DIR = "docs/data/epl"
PLAYERS_DIR = f"{OUT_DIR}/players"

os.makedirs(PLAYERS_DIR, exist_ok=True)

teams = {}
players = {}

team_scorers = defaultdict(lambda: defaultdict(int))
team_yellows = defaultdict(lambda: defaultdict(int))
team_reds = defaultdict(lambda: defaultdict(int))

seen_matches = set()

# =====================================================
# HELPERS
# =====================================================

def clean(v):
    return str(v or "").strip()

def slugify(v):
    return (
        clean(v)
        .lower()
        .replace("&", "and")
        .replace(".", "")
        .replace("'", "")
        .replace("’", "")
        .replace("/", "-")
        .replace(" ", "-")
    )

def ensure_team(team):

    if team not in teams:

        teams[team] = {
            "team": team,
            "games": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0
        }

def ensure_player(player):

    slug = slugify(player)

    if slug not in players:

        players[slug] = {
            "player": player,
            "slug": slug,
            "goals": 0,
            "yellow_cards": 0,
            "red_cards": 0
        }

    return slug

# =====================================================
# MATCH FILES
# =====================================================

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

        match_url = clean(
            game.get("url")
            or os.path.basename(path)
        )

        if match_url in seen_matches:
            continue

        seen_matches.add(match_url)

        home = clean(game.get("home_team"))
        away = clean(game.get("away_team"))

        if not home or not away:
            continue

        ensure_team(home)
        ensure_team(away)

        try:
            hs = int(game.get("home_score", 0) or 0)
        except:
            hs = 0

        try:
            aw = int(game.get("away_score", 0) or 0)
        except:
            aw = 0

        teams[home]["games"] += 1
        teams[away]["games"] += 1

        teams[home]["goals_for"] += hs
        teams[home]["goals_against"] += aw

        teams[away]["goals_for"] += aw
        teams[away]["goals_against"] += hs

        if hs > aw:

            teams[home]["wins"] += 1
            teams[home]["points"] += 3

            teams[away]["losses"] += 1

        elif aw > hs:

            teams[away]["wins"] += 1
            teams[away]["points"] += 3

            teams[home]["losses"] += 1

        else:

            teams[home]["draws"] += 1
            teams[away]["draws"] += 1

            teams[home]["points"] += 1
            teams[away]["points"] += 1

        # =================================================
        # GOALS
        # =================================================

        scorer_seen = set()

        for scorer in game.get("scorers", []):

            if not isinstance(scorer, dict):
                continue

            player = clean(scorer.get("player"))
            team = clean(scorer.get("team"))
            minute = clean(scorer.get("minute"))

            if not player or not team:
                continue

            key = (
                f"{match_url}|"
                f"{team}|"
                f"{player}|"
                f"{minute}"
            )

            if key in scorer_seen:
                continue

            scorer_seen.add(key)

            slug = ensure_player(player)

            players[slug]["goals"] += 1

            team_scorers[team][player] += 1

        # =================================================
        # YELLOWS
        # =================================================

        yellow_seen = set()

        for yellow in game.get("yellow_cards", []):

            if not isinstance(yellow, dict):
                continue

            player = clean(yellow.get("player"))
            team = clean(yellow.get("team"))
            minute = clean(yellow.get("minute"))

            if not player or not team:
                continue

            key = (
                f"{match_url}|"
                f"{team}|"
                f"{player}|"
                f"{minute}"
            )

            if key in yellow_seen:
                continue

            yellow_seen.add(key)

            slug = ensure_player(player)

            players[slug]["yellow_cards"] += 1

            team_yellows[team][player] += 1

        # =================================================
        # REDS
        # =================================================

        red_seen = set()

        for red in game.get("red_cards", []):

            if not isinstance(red, dict):
                continue

            player = clean(red.get("player"))
            team = clean(red.get("team"))
            minute = clean(red.get("minute"))

            if not player or not team:
                continue

            # REAL FIX:
            # exact duplicate rows only

            key = (
                f"{match_url}|"
                f"{team}|"
                f"{player}|"
                f"{minute}"
            )

            if key in red_seen:
                continue

            red_seen.add(key)

            slug = ensure_player(player)

            players[slug]["red_cards"] += 1

            team_reds[team][player] += 1

# =====================================================
# TEAM DIFFERENCE
# =====================================================

for team in teams.values():

    team["goal_difference"] = (
        team["goals_for"]
        - team["goals_against"]
    )

# =====================================================
# SAVE PLAYERS
# =====================================================

players_index = []

for slug, pdata in sorted(players.items()):

    with open(
        f"{PLAYERS_DIR}/{slug}.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            pdata,
            f,
            indent=2,
            ensure_ascii=False
        )

    players_index.append(pdata)

# =====================================================
# TEAM STATS
# =====================================================

team_stats = []

all_teams = (
    set(teams.keys())
    | set(team_scorers.keys())
    | set(team_yellows.keys())
    | set(team_reds.keys())
)

for team in sorted(all_teams):

    # remove impossible totals only

    cleaned_reds = []

    for player, reds in sorted(
        team_reds[team].items(),
        key=lambda x: (-x[1], x[0])
    ):

        if reds > 8:
            continue

        cleaned_reds.append({
            "player": player,
            "red_cards": reds
        })

    team_stats.append({

        "team": team,

        "top_scorers": [
            {
                "player": p,
                "goals": g
            }
            for p, g in sorted(
                team_scorers[team].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]
        ],

        "yellow_cards": [
            {
                "player": p,
                "yellow_cards": y
            }
            for p, y in sorted(
                team_yellows[team].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]
        ],

        "red_cards": cleaned_reds[:20]
    })

# =====================================================
# SAVE
# =====================================================

with open(
    f"{OUT_DIR}/players.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        players_index,
        f,
        indent=2,
        ensure_ascii=False
    )

with open(
    f"{OUT_DIR}/teams.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        sorted(
            teams.values(),
            key=lambda x: (
                -x["points"],
                -x["goal_difference"],
                -x["goals_for"],
                x["team"]
            )
        ),
        f,
        indent=2,
        ensure_ascii=False
    )

with open(
    f"{OUT_DIR}/team_stats.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        team_stats,
        f,
        indent=2,
        ensure_ascii=False
    )

print("MATCHES:", len(seen_matches))
print("PLAYERS:", len(players))
print("TEAMS:", len(teams))
print("DONE")
