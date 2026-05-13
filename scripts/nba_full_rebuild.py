import os
import json

BASE_DIR = "docs/data/nba"

print("REBUILDING NBA SEASON FILES")

for season in os.listdir(BASE_DIR):

    season_dir = os.path.join(BASE_DIR, season)

    if not os.path.isdir(season_dir):
        continue

    if not season.isdigit():
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

        # REGULAR SEASON
        if game_id.startswith("002"):

            game_season = game_id[3:5]

        # PLAYOFFS
        elif game_id.startswith("004"):

            game_season = game_id[3:5]

        else:
            continue

        # ONLY MATCHING SEASON
        if game_season != season[-2:]:
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
