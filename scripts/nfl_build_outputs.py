import os, json, sys
from collections import defaultdict

season = sys.argv[1]

GAME_DIR = f"docs/data/nfl/games/{season}"
SEASON_FILE = f"docs/data/nfl/seasons/{season}.json"
PLAYER_DIR = "docs/data/nfl/players"

os.makedirs(PLAYER_DIR, exist_ok=True)

players = defaultdict(list)
season_games = []

if not os.path.exists(GAME_DIR):
    print("No games folder yet")
    exit()

for file in os.listdir(GAME_DIR):

    if not file.endswith(".json"):
        continue

    game = json.load(open(f"{GAME_DIR}/{file}"))

    season_games.append({
        "game_id": game.get("game_id"),
        "home_team": game.get("home_team"),
        "away_team": game.get("away_team"),
        "home_score": game.get("home_score"),
        "away_score": game.get("away_score")
    })

    for p in game.get("players", []):
        name = p.get("name", "Unknown")

        players[name].append({
            "game_id": game.get("game_id"),
            "stats": p.get("stats", {})
        })


# SAVE SEASON FILE
os.makedirs("docs/data/nfl/seasons", exist_ok=True)

with open(SEASON_FILE, "w") as f:
    json.dump({
        "season": int(season),
        "games": season_games
    }, f)


# SAVE PLAYERS
for name, logs in players.items():
    slug = name.lower().replace(" ", "_")

    with open(f"{PLAYER_DIR}/{slug}.json", "w") as f:
        json.dump({
            "name": name,
            "games": logs
        }, f)

print("Build complete")
