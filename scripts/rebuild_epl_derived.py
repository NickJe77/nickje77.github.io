import os
import json
import shutil
from collections import defaultdict

SEASONS_DIR = "docs/data/epl/seasons"
OUT_DIR = "docs/data/epl"

PLAYERS_DIR = f"{OUT_DIR}/players"

TMP_DIR = "docs/data/epl_tmp"
TMP_PLAYERS_DIR = f"{TMP_DIR}/players"

print("REBUILDING EPL DERIVED FILES")

# =========================================================
# CLEANERS
# =========================================================

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

# =========================================================
# ENSURE OUTPUT FOLDERS
# =========================================================

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PLAYERS_DIR, exist_ok=True)

# =========================================================
# RESET TEMP
# =========================================================

if os.path.exists(TMP_DIR):
    shutil.rmtree(TMP_DIR)

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(TMP_PLAYERS_DIR, exist_ok=True)

# =========================================================
# STORAGE
# =========================================================

players = {}
teams = {}

player_goal_matches = defaultdict(set)
player_yellow_matches = defaultdict(set)
player_red_matches = defaultdict(set)

player_match_data = defaultdict(dict)

team_scorers = defaultdict(lambda: defaultdict(int))
team_yellows = defaultdict(lambda: defaultdict(int))
team_reds = defaultdict(lambda: defaultdict(int))

seen_match_ids = set()

# =========================================================
# LOAD SEASON FILES
# =========================================================

season_files = []

for file in os.listdir(SEASONS_DIR):

    if file.endswith(".json"):

        season_files.append(
            os.path.join(SEASONS_DIR, file)
        )

print(f"SEASON FILES FOUND: {len(season_files)}")

# =========================================================
# PROCESS SEASONS
# =========================================================

for path in sorted(season_files):

    print("PROCESSING:", path)

    try:

        with open(path, "r", encoding="utf-8") as f:
            season_json = json.load(f)

    except Exception as e:

        print("BAD JSON:", path, e)
        continue

    # =====================================================
    # SUPPORT BOTH JSON FORMATS
    # =====================================================

    if isinstance(season_json, dict):

        games = season_json.get("games", [])

        season = clean(
            season_json.get("season")
            or os.path.basename(path).replace(".json", "")
        )

    elif isinstance(season_json, list):

        games = season_json

        season = clean(
            os.path.basename(path).replace(".json", "")
        )

    else:
        continue

    # =====================================================
    # PROCESS GAMES
    # =====================================================

    for game in games:

        if not isinstance(game, dict):
            continue

        match_id = clean(
            game.get("match_id")
            or game.get("id")
            or game.get("game_id")
        )

        if not match_id:
            continue

        if match_id in seen_match_ids:
            continue

        seen_match_ids.add(match_id)

        home = clean(
            game.get("home_team")
            or game.get("home")
        )

        away = clean(
            game.get("away_team")
            or game.get("away")
        )

        if not home or not away:
            continue

        date = clean(game.get("date"))

        try:
            home_score = int(
                game.get("home_score")
                if game.get("home_score") is not None
                else game.get("score_home", 0)
            )
        except:
            home_score = 0

        try:
            away_score = int(
                game.get("away_score")
                if game.get("away_score") is not None
                else game.get("score_away", 0)
            )
        except:
            away_score = 0

        # =================================================
        # TEAM TOTALS
        # =================================================

        for t in [home, away]:

            if t not in teams:

                teams[t] = {
                    "team": t,
                    "games": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0
                }

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

        # =================================================
        # GOALS
        # =================================================

        scorer_seen = set()

        for scorer in (
            game.get("scorers")
            or game.get("goals")
            or []
        ):

            if not isinstance(scorer, dict):
                continue

            player = clean(scorer.get("player"))
            team = clean(scorer.get("team"))
            minute = clean(scorer.get("minute"))

            if not player:
                continue

            dedupe = (
                player.lower(),
                team.lower(),
                minute
            )

            if dedupe in scorer_seen:
                continue

            scorer_seen.add(dedupe)

            slug = slugify(player)

            opponent = away if team == home else home

            if slug not in players:

                players[slug] = {
                    "player": player,
                    "slug": slug
                }

            if match_id not in player_match_data[slug]:

                player_match_data[slug][match_id] = {
                    "match_id": match_id,
                    "season": season,
                    "date": date,
                    "team": team,
                    "opponent": opponent,
                    "goals": 0,
                    "yellow_cards": 0,
                    "red_cards": 0
                }

            player_match_data[slug][match_id]["goals"] += 1

            player_goal_matches[slug].add(match_id)

            team_scorers[team][player] += 1

        # =================================================
        # YELLOWS
        # =================================================

        yellow_seen = set()

        for yellow in (
            game.get("yellow_cards")
            or game.get("yellows")
            or []
        ):

            if not isinstance(yellow, dict):
                continue

            player = clean(yellow.get("player"))
            team = clean(yellow.get("team"))
            minute = clean(yellow.get("minute"))

            if not player:
                continue

            dedupe = (
                player.lower(),
                team.lower(),
                minute
            )

            if dedupe in yellow_seen:
                continue

            yellow_seen.add(dedupe)

            slug = slugify(player)

            opponent = away if team == home else home

            if slug not in players:

                players[slug] = {
                    "player": player,
                    "slug": slug
                }

            if match_id not in player_match_data[slug]:

                player_match_data[slug][match_id] = {
                    "match_id": match_id,
                    "season": season,
                    "date": date,
                    "team": team,
                    "opponent": opponent,
                    "goals": 0,
                    "yellow_cards": 0,
                    "red_cards": 0
                }

            if player_match_data[slug][match_id]["yellow_cards"] < 2:

                player_match_data[slug][match_id]["yellow_cards"] += 1

            player_yellow_matches[slug].add(match_id)

            team_yellows[team][player] += 1

        # =================================================
        # REDS
        # =================================================

        red_seen = set()

        for red in (
            game.get("red_cards")
            or game.get("reds")
            or []
        ):

            if not isinstance(red, dict):
                continue

            player = clean(red.get("player"))
            team = clean(red.get("team"))
            minute = clean(red.get("minute"))

            if not player:
                continue

            dedupe = (
                player.lower(),
                team.lower(),
                minute
            )

            if dedupe in red_seen:
                continue

            red_seen.add(dedupe)

            slug = slugify(player)

            opponent = away if team == home else home

            if slug not in players:

                players[slug] = {
                    "player": player,
                    "slug": slug
                }

            if match_id not in player_match_data[slug]:

                player_match_data[slug][match_id] = {
                    "match_id": match_id,
                    "season": season,
                    "date": date,
                    "team": team,
                    "opponent": opponent,
                    "goals": 0,
                    "yellow_cards": 0,
                    "red_cards": 0
                }

            # MAX 1 RED PER MATCH
            player_match_data[slug][match_id]["red_cards"] = 1

            player_red_matches[slug].add(match_id)

            team_reds[team][player] = len(
                player_red_matches[slug]
            )

# =========================================================
# PLAYER FILES
# =========================================================

players_index = []

for slug, pdata in players.items():

    matches = list(
        player_match_data[slug].values()
    )

    goals = sum(
        m["goals"]
        for m in matches
    )

    yellow_cards = len(
        player_yellow_matches[slug]
    )

    red_cards = len(
        player_red_matches[slug]
    )

    player_output = {
        "player": pdata["player"],
        "slug": slug,
        "goals": goals,
        "yellow_cards": yellow_cards,
        "red_cards": red_cards,
        "matches": matches
    }

    with open(
        f"{TMP_PLAYERS_DIR}/{slug}.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            player_output,
            f,
            indent=2,
            ensure_ascii=False
        )

    players_index.append({
        "player": pdata["player"],
        "slug": slug,
        "goals": goals,
        "yellow_cards": yellow_cards,
        "red_cards": red_cards,
        "matches": len(matches)
    })

# =========================================================
# TEAM STATS
# =========================================================

team_stats_output = []

for team in sorted(team_scorers.keys()):

    team_stats_output.append({

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

        "red_cards": [
            {
                "player": p,
                "red_cards": r
            }
            for p, r in sorted(
                team_reds[team].items(),
                key=lambda x: (-x[1], x[0])
            )[:20]
        ]
    })

# =========================================================
# SAVE FILES
# =========================================================

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
            key=lambda x: x["team"]
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
        team_stats_output,
        f,
        indent=2,
        ensure_ascii=False
    )

# =========================================================
# PLAYER FILES
# =========================================================

if os.path.exists(PLAYERS_DIR):
    shutil.rmtree(PLAYERS_DIR)

os.makedirs(PLAYERS_DIR, exist_ok=True)

for file in os.listdir(TMP_PLAYERS_DIR):

    shutil.move(
        os.path.join(TMP_PLAYERS_DIR, file),
        os.path.join(PLAYERS_DIR, file)
    )

# =========================================================
# DEBUG
# =========================================================

print("PLAYERS FOUND:", len(players))
print("PLAYER MATCH DATA:", len(player_match_data))
print("GOAL PLAYERS:", len(player_goal_matches))
print("YELLOW PLAYERS:", len(player_yellow_matches))
print("RED PLAYERS:", len(player_red_matches))

print("TMP PLAYER FILES:")
print(os.listdir(TMP_PLAYERS_DIR)[:20])

# =========================================================
# CLEANUP
# =========================================================

shutil.rmtree(TMP_DIR, ignore_errors=True)

print("DONE")
