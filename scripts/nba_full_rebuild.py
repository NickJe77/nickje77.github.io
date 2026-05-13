import os
import json
from glob import glob

BASE_DIR = "docs/data/nba"

print("NBA HARD REBUILD STARTED")
print("=" * 70)

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def safe_int(v):
    try:
        return int(float(v))
    except:
        return 0

season_dirs = sorted([
    d for d in os.listdir(BASE_DIR)
    if os.path.isdir(os.path.join(BASE_DIR, d))
])

for season in season_dirs:

    print(f"\nPROCESSING {season}")

    season_path = os.path.join(BASE_DIR, season)

    all_json = glob(
        os.path.join(season_path, "**", "*.json"),
        recursive=True
    )

    # ALSO SCAN GLOBAL BOXSCORE AREA
    global_boxscores = glob(
        os.path.join(BASE_DIR, "boxscores", season, "**", "*.json"),
        recursive=True
    )

    all_json.extend(global_boxscores)

    # REMOVE NON GAME FILES
    all_json = [
        x for x in all_json
        if not any(bad in x.lower() for bad in [
            "index.json",
            "players.json",
            "teams.json",
            "standings.json",
            "schedule.json"
        ])
    ]

    print(f"FOUND {len(all_json)} JSON FILES")

    rebuilt = []

    for path in all_json:

        raw = load_json(path)

        if raw is None:
            continue

        # -----------------------------------------
        # HANDLE LIST FILES
        # -----------------------------------------

        if isinstance(raw, list):

            for game in raw:

                if not isinstance(game, dict):
                    continue

                # VERY IMPORTANT:
                # ONLY ACCEPT ACTUAL GAMES
                possible_home = (
                    game.get("home_team")
                    or game.get("homeTeam")
                    or game.get("home")
                    or game.get("team1")
                    or ""
                )

                possible_away = (
                    game.get("away_team")
                    or game.get("awayTeam")
                    or game.get("away")
                    or game.get("team2")
                    or ""
                )

                if not possible_home or not possible_away:
                    continue

                rebuilt.append({
                    "game_id": str(
                        game.get("game_id")
                        or game.get("id")
                        or game.get("gamePk")
                        or os.path.splitext(os.path.basename(path))[0]
                    ),
                    "date": (
                        game.get("date")
                        or game.get("game_date")
                        or game.get("datetime")
                        or ""
                    ),
                    "home_team": possible_home,
                    "away_team": possible_away,
                    "home_score": safe_int(
                        game.get("home_score")
                        or game.get("homeScore")
                        or game.get("score1")
                        or 0
                    ),
                    "away_score": safe_int(
                        game.get("away_score")
                        or game.get("awayScore")
                        or game.get("score2")
                        or 0
                    ),
                    "venue": (
                        game.get("venue")
                        or game.get("arena")
                        or ""
                    ),
                    "type": (
                        "Playoffs"
                        if "playoff" in json.dumps(game).lower()
                        else "Regular Season"
                    ),
                    "game_file": os.path.basename(path)
                })

        # -----------------------------------------
        # HANDLE SINGLE GAME FILES
        # -----------------------------------------

        elif isinstance(raw, dict):

            possible_home = (
                raw.get("home_team")
                or raw.get("homeTeam")
                or raw.get("home")
                or raw.get("team1")
                or ""
            )

            possible_away = (
                raw.get("away_team")
                or raw.get("awayTeam")
                or raw.get("away")
                or raw.get("team2")
                or ""
            )

            if not possible_home or not possible_away:
                continue

            rebuilt.append({
                "game_id": str(
                    raw.get("game_id")
                    or raw.get("id")
                    or raw.get("gamePk")
                    or os.path.splitext(os.path.basename(path))[0]
                ),
                "date": (
                    raw.get("date")
                    or raw.get("game_date")
                    or raw.get("datetime")
                    or ""
                ),
                "home_team": possible_home,
                "away_team": possible_away,
                "home_score": safe_int(
                    raw.get("home_score")
                    or raw.get("homeScore")
                    or raw.get("score1")
                    or 0
                ),
                "away_score": safe_int(
                    raw.get("away_score")
                    or raw.get("awayScore")
                    or raw.get("score2")
                    or 0
                ),
                "venue": (
                    raw.get("venue")
                    or raw.get("arena")
                    or ""
                ),
                "type": (
                    "Playoffs"
                    if "playoff" in json.dumps(raw).lower()
                    else "Regular Season"
                ),
                "game_file": os.path.basename(path)
            })

    # -----------------------------------------
    # REMOVE DUPLICATES
    # -----------------------------------------

    deduped = {}

    for game in rebuilt:
        deduped[game["game_id"]] = game

    rebuilt = list(deduped.values())

    rebuilt.sort(key=lambda x: x.get("date", ""))

    index_path = os.path.join(season_path, "index.json")

    save_json(index_path, rebuilt)

    print(f"REBUILT {len(rebuilt)} GAMES")

print("\nNBA HARD REBUILD COMPLETE")
