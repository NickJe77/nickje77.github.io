import os
import json

SEASON = "2026"

BASE_DIR = os.getcwd()

BOX_DIR = os.path.join(
    BASE_DIR,
    "docs",
    "data",
    "nba",
    "boxscores",
    SEASON
)

SEASON_DIR = os.path.join(
    BASE_DIR,
    "docs",
    "data",
    "nba",
    SEASON
)

INDEX_FILE = os.path.join(
    SEASON_DIR,
    "index.json"
)

os.makedirs(BOX_DIR, exist_ok=True)
os.makedirs(SEASON_DIR, exist_ok=True)

print("READING EXISTING FILES")

games = []

files = sorted(
    f for f in os.listdir(BOX_DIR)
    if f.endswith(".json")
)

print(f"FILES FOUND: {len(files)}")

for filename in files:

    path = os.path.join(BOX_DIR, filename)

    try:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:

        print("BAD FILE:", filename, e)

        continue

    game = data.get("game", {})

    if not game:
        continue

    game_id = filename.replace(".json", "")

    home_team = (
        game.get("homeTeam", {})
        .get("teamName", "")
    )

    away_team = (
        game.get("awayTeam", {})
        .get("teamName", "")
    )

    game_date = (
        game.get("gameEt")
        or game.get("gameTimeUTC")
        or ""
    )

    games.append({
        "game_id": game_id,
        "game_file": filename,
        "home_team": home_team,
        "away_team": away_team,
        "date": game_date
    })

games.sort(
    key=lambda x: (x.get("date", ""), x.get("game_id", ""))
)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(games, f, indent=2)

print(f"INDEX BUILT: {len(games)} games")
print("DONE")
