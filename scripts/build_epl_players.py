import os
import json

SEASONS_DIR = "docs/data/epl/seasons"

print("DEBUGGING EPL SEASON STRUCTURE")

season_files = sorted(
    f for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
)

if not season_files:
    raise Exception("NO SEASON FILES FOUND")

for season_file in season_files:

    season_path = os.path.join(SEASONS_DIR, season_file)

    print(f"\nREADING: {season_file}")

    try:
        with open(season_path, "r", encoding="utf-8") as f:
            games = json.load(f)
    except Exception as e:
        print("FAILED TO LOAD JSON")
        print(e)
        continue

    print(f"TYPE: {type(games)}")

    if isinstance(games, dict):

        print("\nTOP LEVEL KEYS:")
        print(list(games.keys())[:50])

        # try common wrappers
        possible_lists = [
            games.get("games"),
            games.get("matches"),
            games.get("fixtures"),
            games.get("data")
        ]

        found = False

        for item in possible_lists:

            if isinstance(item, list) and item:

                print("\nFOUND GAME LIST")

                game = item[0]

                print("\nGAME KEYS:")
                print(list(game.keys())[:100])

                print("\nFULL SAMPLE GAME:")
                print(json.dumps(game, indent=2)[:10000])

                found = True
                break

        if found:
            break

    elif isinstance(games, list):

        print(f"\nTOTAL GAMES: {len(games)}")

        if not games:
            continue

        game = games[0]

        print("\nGAME KEYS:")
        print(list(game.keys())[:100])

        print("\nFULL SAMPLE GAME:")
        print(json.dumps(game, indent=2)[:10000])

        break

print("\nDONE")
