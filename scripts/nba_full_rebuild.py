import os
import json

BASE_DIR = "docs/data/nba"

print("REBUILDING MODERN NBA SEASONS")

MODERN_SEASONS = [
    "2024",
    "2025",
    "2026"
]

for season in MODERN_SEASONS:

    season_dir = os.path.join(BASE_DIR, season)

    if not os.path.isdir(season_dir):
        continue

    games = []

    print(f"PROCESSING {season}")

    for filename in os.listdir(season_dir):

        if not filename.endswith(".json"):
            continue

        if filename in ["games.json", "index.json"]:
            continue

        path = os.path.join(season_dir, filename)

        try:

            with open(path, "r", encoding="utf-8") as f:
                game = json.load(f)

        except:
            continue

        if not isinstance(game, dict):
            continue

        game_id = str(game.get("game_id", ""))

        if not game_id:
            continue

        # ONLY KEEP MATCHING SEASON

        if season == "2024":

            if not (
                game_id.startswith("00224")
                or game_id.startswith("00424")
            ):
                continue

        elif season == "2025":

            if not (
                game_id.startswith("00225")
                or game_id.startswith("00425")
            ):
                continue

        elif season == "2026":

            if not (
                game_id.startswith("00226")
                or game_id.startswith("00426")
            ):
                continue

        games.append(game)

    games.sort(
        key=lambda x: x.get("date", "")
    )

    out_file = os.path.join(
        season_dir,
        "games.json"
    )

    with open(
        out_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            games,
            f,
            indent=2
        )

    print(f"{season} = {len(games)} games")

print("DONE")
