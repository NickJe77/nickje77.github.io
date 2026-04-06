import json
from pathlib import Path

print("MLB SEASON CONVERTER STARTED")

SEASONS_DIR = Path("docs/data/baseball/seasons")

def convert_season(file_path):

    with open(file_path) as f:
        data = json.load(f)

    # already correct format (list of objects)
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        print(f"SKIP (already correct): {file_path.name}")
        return

    # wrapped format
    if isinstance(data, dict) and "games" in data:
        games = data["games"]
    else:
        games = data

    if not isinstance(games, list) or len(games) == 0:
        print(f"SKIP (empty/bad): {file_path.name}")
        return

    # if already objects inside
    if isinstance(games[0], dict):
        print(f"SKIP (already object list): {file_path.name}")
        return

    print(f"CONVERTING: {file_path.name}")

    new_games = []

    for g in games:
        try:
            new_games.append({
                "game_id": g[0],
                "date": g[1],
                "home_team": g[3],
                "away_team": g[4],
                "venue": g[5],
                "away_score": g[7],
                "home_score": g[8]
            })
        except Exception as e:
            print(f"⚠️ SKIPPED GAME IN {file_path.name}: {e}")

    # overwrite with new format
    with open(file_path, "w") as f:
        json.dump(new_games, f, indent=2)

    print(f"DONE: {file_path.name}")


# RUN ALL SEASONS
for file in SEASONS_DIR.glob("*.json"):
    convert_season(file)

print("ALL SEASONS CONVERTED")
