import os
import json
from glob import glob

BASE_DIR = "docs/data/nba"

print("REBUILDING NBA SEASON INDEXES FROM EXISTING GAME FILES")
print("NO GAME FILES WILL BE OVERWRITTEN")
print("=" * 60)

def safe_int(v):
    try:
        return int(float(v))
    except:
        return 0

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"FAILED TO LOAD {path}: {e}")
        return None

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

season_folders = sorted([
    d for d in os.listdir(BASE_DIR)
    if os.path.isdir(os.path.join(BASE_DIR, d))
])

total_games = 0

for season in season_folders:

    season_path = os.path.join(BASE_DIR, season)

    print(f"\nPROCESSING SEASON {season}")

    possible_paths = [
        os.path.join(season_path, "*.json"),
        os.path.join(season_path, "games", "*.json"),
        os.path.join(season_path, "boxscores", "*.json"),
        os.path.join(BASE_DIR, "boxscores", season, "*.json"),
    ]

    game_files = []

    for p in possible_paths:
        game_files.extend(glob(p))

    # REMOVE INDEX / PLAYER / TEAM FILES
    game_files = [
        g for g in game_files
        if not any(x in os.path.basename(g).lower() for x in [
            "index",
            "players",
            "teams",
            "standings"
        ])
    ]

    unique_files = sorted(list(set(game_files)))

    print(f"FOUND {len(unique_files)} GAME FILES")

    rebuilt_games = []

    for game_file in unique_files:

        raw = load_json(game_file)

        if not raw:
            continue

        games_to_process = []

        # HANDLE SINGLE OBJECT
        if isinstance(raw, dict):
            games_to_process = [raw]

        # HANDLE LIST OF GAMES
        elif isinstance(raw, list):
            games_to_process = raw

        else:
            continue

        for game in games_to_process:

            if not isinstance(game, dict):
                continue

            try:

                # TEAM NAMES
                home_team = (
                    game.get("home_team")
                    or game.get("home")
                    or game.get("team1")
                    or game.get("homeTeam")
                    or game.get("home_team_name")
                    or ""
                )

                away_team = (
                    game.get("away_team")
                    or game.get("away")
                    or game.get("team2")
                    or game.get("awayTeam")
                    or game.get("away_team_name")
                    or ""
                )

                # SCORES
                home_score = (
                    game.get("home_score")
                    or game.get("homeScore")
                    or game.get("score1")
                    or game.get("home_points")
                    or 0
                )

                away_score = (
                    game.get("away_score")
                    or game.get("awayScore")
                    or game.get("score2")
                    or game.get("away_points")
                    or 0
                )

                # DATE
                date = (
                    game.get("date")
                    or game.get("game_date")
                    or game.get("start_date")
                    or game.get("datetime")
                    or ""
                )

                # GAME ID
                game_id = (
                    game.get("game_id")
                    or game.get("id")
                    or game.get("gamePk")
                    or os.path.splitext(os.path.basename(game_file))[0]
                )

                # VENUE
                venue = (
                    game.get("venue")
                    or game.get("arena")
                    or game.get("stadium")
                    or ""
                )

                # PLAYOFF DETECTION
                playoff = False

                text_blob = json.dumps(game).lower()

                playoff_terms = [
                    "playoff",
                    "playoffs",
                    "western conference finals",
                    "eastern conference finals",
                    "nba finals",
                    "conference semifinals",
                    "conference quarterfinals",
                    "play in",
                    "play-in",
                    "round 1",
                    "round 2"
                ]

                if any(x in text_blob for x in playoff_terms):
                    playoff = True

                rebuilt_games.append({
                    "game_id": str(game_id),
                    "date": date,
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_score": safe_int(home_score),
                    "away_score": safe_int(away_score),
                    "venue": venue,
                    "playoff": playoff,
                    "game_file": os.path.basename(game_file)
                })

            except Exception as e:
                print(f"FAILED PROCESSING GAME IN {game_file}: {e}")

    # REMOVE DUPLICATES
    deduped = {}
    for g in rebuilt_games:
        deduped[g["game_id"]] = g

    rebuilt_games = list(deduped.values())

    # SORT BY DATE
    rebuilt_games.sort(key=lambda x: x.get("date", ""))

    # SAVE INDEX
    index_path = os.path.join(season_path, "index.json")

    save_json(index_path, rebuilt_games)

    print(f"REBUILT index.json WITH {len(rebuilt_games)} GAMES")

    total_games += len(rebuilt_games)

print("\n" + "=" * 60)
print(f"TOTAL GAMES INDEXED: {total_games}")
print("NBA REBUILD COMPLETE")
