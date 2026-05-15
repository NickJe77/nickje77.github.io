import os
import json

SEASONS_DIR = "docs/data/epl/seasons"

print("DEBUGGING EPL SEASON STRUCTURE")

season_files = sorted([
    os.path.join(SEASONS_DIR, f)
    for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
])

print(f"FOUND {len(season_files)} SEASON FILES")

for path in season_files:

    print("\n================================================")
    print("FILE:", path)
    print("================================================")

    try:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:

        print("FAILED TO LOAD:", e)
        continue

    print("\nTOP LEVEL TYPE:")
    print(type(data))

    # =====================================================
    # DICT FORMAT
    # =====================================================

    if isinstance(data, dict):

        print("\nTOP LEVEL KEYS:")
        print(list(data.keys())[:50])

        games = data.get("games")

        print("\nGAMES TYPE:")
        print(type(games))

        if isinstance(games, list) and games:

            print("\nFIRST GAME SAMPLE:")
            print(json.dumps(games[0], indent=2)[:5000])

            break

    # =====================================================
    # LIST FORMAT
    # =====================================================

    elif isinstance(data, list):

        print("\nLIST LENGTH:")
        print(len(data))

        if data:

            print("\nFIRST ITEM TYPE:")
            print(type(data[0]))

            print("\nFIRST GAME SAMPLE:")
            print(json.dumps(data[0], indent=2)[:5000])

            break

print("\nDONE")
