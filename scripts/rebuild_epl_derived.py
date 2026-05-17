import os
import json

MATCHES_DIR = "docs/data/epl/matches"
OUT_DIR = "docs/data/epl"

TEAMS_FILE = f"{OUT_DIR}/teams.json"

print("REBUILDING EPL TEAMS")

teams = {}

seen_matches = set()

# =====================================================
# HELPERS
# =====================================================

def clean(v):
    return str(v or "").strip()

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

# =====================================================
# LOAD MATCHES
# =====================================================

match_files = []

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in files:

        if file.endswith(".json"):

            match_files.append(
                os.path.join(root, file)
            )

print("MATCH FILES:", len(match_files))

# =====================================================
# PROCESS
# =====================================================

for path in sorted(match_files):

    try:

        with open(path, "r", encoding="utf-8") as f:
            game = json.load(f)

    except Exception as e:

        print("FAILED:", path, e)
        continue

    if not isinstance(game, dict):
        continue

    home_team = clean(
        game.get("home_team")
    )

    away_team = clean(
        game.get("away_team")
    )

    if not home_team or not away_team:
        continue

    match_key = clean(
        game.get("url")
        or f"{home_team}_{away_team}_{os.path.basename(path)}"
    )

    if match_key in seen_matches:
        continue

    seen_matches.add(match_key)

    ensure_team(home_team)
    ensure_team(away_team)

    try:
        home_score = int(
            game.get("home_score", 0)
        )
    except:
        home_score = 0

    try:
        away_score = int(
            game.get("away_score", 0)
        )
    except:
        away_score = 0

    # =================================================
    # GAMES
    # =================================================

    teams[home_team]["games"] += 1
    teams[away_team]["games"] += 1

    # =================================================
    # GOALS
    # =================================================

    teams[home_team]["goals_for"] += home_score
    teams[home_team]["goals_against"] += away_score

    teams[away_team]["goals_for"] += away_score
    teams[away_team]["goals_against"] += home_score

    # =================================================
    # RESULTS
    # =================================================

    if home_score > away_score:

        teams[home_team]["wins"] += 1
        teams[home_team]["points"] += 3

        teams[away_team]["losses"] += 1

    elif away_score > home_score:

        teams[away_team]["wins"] += 1
        teams[away_team]["points"] += 3

        teams[home_team]["losses"] += 1

    else:

        teams[home_team]["draws"] += 1
        teams[away_team]["draws"] += 1

        teams[home_team]["points"] += 1
        teams[away_team]["points"] += 1

# =====================================================
# GOAL DIFFERENCE
# =====================================================

for team in teams.values():

    team["goal_difference"] = (
        team["goals_for"]
        - team["goals_against"]
    )

# =====================================================
# SORT
# =====================================================

output = sorted(
    teams.values(),
    key=lambda x: (
        -x["points"],
        -x["goal_difference"],
        -x["goals_for"],
        x["team"]
    )
)

# =====================================================
# SAVE
# =====================================================

with open(
    TEAMS_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        indent=2,
        ensure_ascii=False
    )

print("TEAMS:", len(output))
print("MATCHES:", len(seen_matches))
print("DONE")
