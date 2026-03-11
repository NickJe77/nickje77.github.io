import json
import os

BASE_DIR = "docs/data/nba"

print("NBA build season summaries starting")


def sort_key(game):
    return game.get("date", "")


for season in os.listdir(BASE_DIR):
    season_path = os.path.join(BASE_DIR, season)

    if not season.isdigit():
        continue
    if not os.path.isdir(season_path):
        continue

    index_path = os.path.join(season_path, "index.json")
    if not os.path.exists(index_path):
        continue

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    summaries = []

    for game_id in index.get("games", []):
        game_file = os.path.join(season_path, f"{game_id}.json")
        if not os.path.exists(game_file):
            continue

        with open(game_file, "r", encoding="utf-8") as f:
            game = json.load(f)

        game_type = game.get("game_type", "")
        if game_type in ("Preseason", "All-Star"):
            continue

        summaries.append({
            "game_id": game.get("game_id", ""),
            "date": game.get("date", ""),
            "game_type": game_type,
            "home_team": game.get("home_team", ""),
            "away_team": game.get("away_team", ""),
            "home_score": game.get("home_score", 0),
            "away_score": game.get("away_score", 0),
            "arena": game.get("arena", "")
        })

    summaries.sort(key=sort_key, reverse=True)

    games_path = os.path.join(season_path, "games.json")
    with open(games_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

    print(f"Built {games_path} with {len(summaries)} games")

print("NBA build season summaries finished")
