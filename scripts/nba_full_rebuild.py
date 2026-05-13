import os
import json
from glob import glob

BASE_DIR = "docs/data/nba"

print("NBA LEGACY STRUCTURE REBUILD")
print("=" * 80)

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def safe_int(v):
    try:
        return int(float(v))
    except:
        return 0

def extract_games(raw, source_file):

    games = []

    # -----------------------------
    # SINGLE GAME FILE
    # -----------------------------
    if isinstance(raw, dict):

        # DIRECT GAME FILE
        if any(k in raw for k in [
            "home_team",
            "away_team",
            "homeTeam",
            "awayTeam",
            "team1",
            "team2"
        ]):
            games.append(raw)

        # NESTED GAMES ARRAY
        elif "games" in raw and isinstance(raw["games"], list):
            games.extend(raw["games"])

    # -----------------------------
    # ARRAY OF GAMES
    # -----------------------------
    elif isinstance(raw, list):
        games.extend(raw)

    cleaned = []

    for g in games:

        if not isinstance(g, dict):
            continue

        home_team = (
            g.get("home_team")
            or g.get("homeTeam")
            or g.get("home")
            or g.get("team1")
            or g.get("home_team_name")
            or ""
        )

        away_team = (
            g.get("away_team")
            or g.get("awayTeam")
            or g.get("away")
            or g.get("team2")
            or g.get("away_team_name")
            or ""
        )

        # MUST HAVE BOTH TEAMS
        if not home_team or not away_team:
            continue

        game_id = (
            g.get("game_id")
            or g.get("id")
            or g.get("gamePk")
            or os.path.splitext(os.path.basename(source_file))[0]
        )

        date = (
            g.get("date")
            or g.get("game_date")
            or g.get("datetime")
            or g.get("start_date")
            or ""
        )

        venue = (
            g.get("venue")
            or g.get("arena")
            or g.get("stadium")
            or ""
        )

        home_score = (
            g.get("home_score")
            or g.get("homeScore")
            or g.get("score1")
            or g.get("home_points")
            or 0
        )

        away_score = (
            g.get("away_score")
            or g.get("awayScore")
            or g.get("score2")
            or g.get("away_points")
            or 0
        )

        blob = json.dumps(g).lower()

        playoff = any(x in blob for x in [
            "playoff",
            "nba finals",
            "conference finals",
            "semifinals",
            "round 1",
            "round 2",
            "play-in"
        ])

        cleaned.append({
            "game_id": str(game_id),
            "date": date,
            "home_team": home_team,
            "away_team": away_team,
            "home_score": safe_int(home_score),
            "away_score": safe_int(away_score),
            "venue": venue,
            "playoff": playoff,
            "game_file": os.path.basename(source_file)
        })

    return cleaned

season_dirs = sorted([
    d for d in os.listdir(BASE_DIR)
    if os.path.isdir(os.path.join(BASE_DIR, d))
])

grand_total = 0

for season in season_dirs:

    season_path = os.path.join(BASE_DIR, season)

    print(f"\nPROCESSING {season}")

    json_files = glob(
        os.path.join(season_path, "**", "*.json"),
        recursive=True
    )

    json_files += glob(
        os.path.join(BASE_DIR, "boxscores", season, "**", "*.json"),
        recursive=True
    )

    # REMOVE NON GAME FILES
    json_files = [
        x for x in json_files
        if not any(bad in x.lower() for bad in [
            "index.json",
            "players.json",
            "teams.json",
            "standings.json",
            "schedule.json"
        ])
    ]

    print(f"FOUND {len(json_files)} JSON FILES")

    rebuilt = []

    for jf in json_files:

        raw = load_json(jf)

        if raw is None:
            continue

        games = extract_games(raw, jf)

        rebuilt.extend(games)

    # REMOVE DUPLICATES
    deduped = {}

    for g in rebuilt:
        deduped[g["game_id"]] = g

    rebuilt = list(deduped.values())

    # SORT
    rebuilt.sort(key=lambda x: x.get("date", ""))

    # SAVE
    index_path = os.path.join(season_path, "index.json")

    save_json(index_path, rebuilt)

    print(f"REBUILT {len(rebuilt)} GAMES")

    grand_total += len(rebuilt)

print("\n" + "=" * 80)
print(f"TOTAL NBA GAMES INDEXED: {grand_total}")
print("NBA REBUILD COMPLETE")
