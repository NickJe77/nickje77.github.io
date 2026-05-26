import json
import os

BOXSCORES_BASE = "docs/data/baseball/boxscores"
SEASONS_BASE = "docs/data/baseball/seasons"


def count_runs(event_string):
    if "." not in event_string:
        return 0
    advancement = event_string.split(".", 1)[1]
    moves = advancement.split(";")
    runs = 0
    for move in moves:
        if "-H" in move:
            runs += 1
    return runs


def parse_scores_from_events(events):
    home_score = 0
    away_score = 0
    for event in events:
        if not isinstance(event, list) or len(event) < 7:
            continue
        if event[0] != "play":
            continue
        batting_side = event[2]
        event_string = event[6]
        runs = count_runs(event_string)
        if runs > 0:
            if batting_side == "0":
                away_score += runs
            else:
                home_score += runs
    return away_score, home_score


# -------------------------
# PATCH BOXSCORE FILES
# -------------------------

for season in sorted(os.listdir(BOXSCORES_BASE)):

    season_path = os.path.join(BOXSCORES_BASE, season)

    if not os.path.isdir(season_path):
        continue

    season_patched = 0

    for filename in os.listdir(season_path):

        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(season_path, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                game = json.load(f)
        except Exception as e:
            print(f"  ERROR reading {filepath}: {e}")
            continue

        events = game.get("events", [])
        if not events:
            continue

        current_away = game.get("away_score", 0)
        current_home = game.get("home_score", 0)

        if current_away != 0 or current_home != 0:
            continue

        away_score, home_score = parse_scores_from_events(events)

        if away_score == 0 and home_score == 0:
            continue

        game["away_score"] = away_score
        game["home_score"] = home_score

        if isinstance(game.get("away_team"), dict):
            game["away_team"]["score"] = away_score
        if isinstance(game.get("home_team"), dict):
            game["home_team"]["score"] = home_score

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(game, f, ensure_ascii=False, indent=2)

        season_patched += 1

    if season_patched:
        print(f"{season}: patched {season_patched} boxscores")


# -------------------------
# PATCH SEASON FILES
# -------------------------

for filename in os.listdir(SEASONS_BASE):

    if not filename.endswith(".json"):
        continue

    season = filename.replace(".json", "")
    path = os.path.join(SEASONS_BASE, filename)

    try:
        with open(path, "r") as f:
            games = json.load(f)
    except Exception as e:
        print(f"ERROR reading {path}: {e}")
        continue

    changed = 0

    for game in games:

        if game.get("away_score", 0) != 0 or game.get("home_score", 0) != 0:
            continue

        game_file = game.get("game_file", "")
        if not game_file:
            continue

        boxscore_path = os.path.join(
            BOXSCORES_BASE,
            season,
            game_file
        )

        if not os.path.exists(boxscore_path):
            continue

        try:
            with open(boxscore_path, "r") as f:
                box = json.load(f)
        except:
            continue

        away = box.get("away_score", 0)
        home = box.get("home_score", 0)

        if away == 0 and home == 0:
            continue

        game["away_score"] = away
        game["home_score"] = home
        changed += 1

    with open(path, "w") as f:
        json.dump(games, f, ensure_ascii=False, indent=2)

    if changed:
        print(f"Season {season}: updated {changed} scores")

print("\nDone.")
