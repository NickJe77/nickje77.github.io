import json
import os

BASE_DIR = "docs/data/nba"
SEASON = "2025"

print("Building summary for season", SEASON)

season_path = os.path.join(BASE_DIR, SEASON)
index_path = os.path.join(season_path, "index.json")

with open(index_path) as f:
    index = json.load(f)

def get_game_type(game):
    vals = [
        game.get("game_type"),
        game.get("season_type"),
        game.get("type"),
        game.get("status"),
        game.get("name")
    ]

    vals = [str(v).lower() for v in vals if v]
    joined = " ".join(vals)

    # PLAY-IN
    if "play-in" in joined or "play in" in joined:
        return "Play-In"

    # PLAYOFFS
    if any(x in joined for x in ["playoff", "final", "conference", "round"]):
        return "Playoffs"

    # FALLBACK: DATE (very reliable for NBA)
    date = game.get("date", "")
    if date >= "2026-04-15":
        return "Playoffs"

    return "Regular Season"


summaries = []

for game_id in index["games"]:

    game_file = os.path.join(season_path, f"{game_id}.json")

    if not os.path.exists(game_file):
        continue

    with open(game_file) as f:
        game = json.load(f)

    game_type = get_game_type(game)

    # skip preseason + all star
    if game_type in ("Preseason", "All-Star"):
        continue

    summaries.append({
        "game_id": game.get("game_id",""),
        "date": game.get("date",""),
        "game_type": game_type,
        "home_team": game.get("home_team",""),
        "away_team": game.get("away_team",""),
        "home_score": game.get("home_score",0),
        "away_score": game.get("away_score",0),
        "arena": game.get("arena","")
    })

summaries.sort(key=lambda x: x["date"], reverse=True)

games_path = os.path.join(season_path, "games.json")

with open(games_path,"w") as f:
    json.dump(summaries,f,indent=2)

print("Built", games_path, "with", len(summaries), "games")
