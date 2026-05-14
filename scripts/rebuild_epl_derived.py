import os
import json
import shutil
from collections import defaultdict

SEASONS_DIR = "docs/data/epl/seasons"
OUT_DIR = "docs/data/epl"

PLAYERS_DIR = f"{OUT_DIR}/players"

TMP_DIR = "docs/data/epl_tmp"
TMP_PLAYERS_DIR = f"{TMP_DIR}/players"

print("REBUILDING EPL DERIVED FILES FROM SEASON FILES")

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
# TEMP
# =========================================================

if os.path.exists(TMP_DIR):
    shutil.rmtree(TMP_DIR)

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

    print("PROCESSING", path)

    try:

        with open(path, "r", encoding="utf-8") as f:
            season_json = json.load(f)

    except Exception as e:

        print("BAD JSON:", path, e)
        continue

    games = season_json.get("games", [])

    season = clean(
        season_json.get("season")
    )

    for game in games:

        match_id = clean(
            game.get("match_id")
            or game.get("id")
        )

        if not match_id:
            continue

        # =================================================
        # GLOBAL MATCH DEDUPE
        # =================================================

        if match_id in seen_match_ids:
            continue

        seen_match_ids.add(match_id)

        date = clean(game.get("date"))

        home = clean(
            game.get("home_team")
            or game.get("home")
        )

        away = clean(
            game.get("away_team")
            or game.get("away")
        )

        home_score = (
            game.get("home_score")
            if game.get("home_score") is not None
            else game.get("score_home")
        )

        away_score = (
            game.get("away_score")
            if game.get("away_score") is not None
            else game.get("score_away")
        )

        try:
            home_score = int(home_score or 0)
        except:
            home_score = 0

        try:
            away_score = int(away_score or 0)
        except:
            away_score = 0

        # ================================================
        # TEAMS
        # ================================================

        for t in [home, away]:

            if not t:
                continue

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

        if home:

            teams[home]["games"] += 1
            teams[home]["goals_for"] += home_score
            teams[home]["goals_against"] += away_score

            if home_score > away_score:
                teams[home]["wins"] += 1

            elif home_score == away_score:
                teams[home]["draws"] += 1

            else:
                teams[home]["losses"] += 1

        if away:

            teams[away]["games"] += 1
            teams[away]["goals_for"] += away_score
            teams[away]["goals_against"] += home_score

            if away_score > home_score:
                teams[away]["wins"] += 1

            elif away_score == home_score:
                teams[away]["draws"] += 1

            else:
                teams[away]["losses"] += 1

        # ================================================
        # GOALS
        # ================================================

        scorer_seen = set()

        for scorer in game.get("scorers", []) or []:

            if not isinstance(scorer, dict):
                continue

            player = clean(scorer.get("player"))
            team = clean(scorer.get("team"))
            minute = clean(scorer.get("minute"))

            if not player:
                continue

            dedupe_key = (
                player.lower(),
                team.lower(),
                minute
            )

            if dedupe_key in scorer_seen:
                continue

            scorer_seen.add(dedupe_key)

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

        # ================================================
        # YELLOWS
        # ================================================

        yellow_seen = set()

        for yellow in game.get("yellow_cards", []) or []:

            if not isinstance(yellow, dict):
                continue

            player = clean(yellow.get("player"))
            team = clean(yellow.get("team"))
            minute = clean(yellow.get("minute"))

            if not player:
                continue

            dedupe_key = (
                player.lower(),
                team.lower(),
                minute
            )

            if dedupe_key in yellow_seen:
                continue

            yellow_seen.add(dedupe_key)

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

        # ================================================
        # REDS
        # ================================================

        red_seen = set()

        for red in game.get("red_cards", []) or []:

            if not isinstance(red, dict):
                continue

            player = clean(red.get("player"))
            team = clean(red.get("team"))
            minute = clean(red.get("minute"))

            if not player:
                continue

            dedupe_key = (
                player.lower(),
                team.lower(),
                minute
            )

            if dedupe_key in red_seen:
                continue

            red_seen.add(dedupe_key)

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

            # ONLY 1 RED MAX PER MATCH
            player_match_data[slug][match_id]["red_cards"] = 1

            player_red_matches[slug].add(match_id)

            team_reds[team][player] = len(
                player_red_matches[slug]
            )

# =========================================================
# PLAYER FILES
# =========================================================

players_index = []

for slug, pdata in sorted(players.items()):

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
# SAVE
# =========================================================

with open(
    f"{TMP_DIR}/players.json",
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
    f"{TMP_DIR}/teams.json",
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
    f"{TMP_DIR}/team_stats.json",
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
# MOVE INTO PLACE
# =========================================================

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
