import os
import json

SEASONS_DIR = "docs/data/epl/seasons"

print("DEBUGGING EPL DATA")

files = sorted([
    f for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
])

print("FILES FOUND:", len(files))

for filename in files:

    path = os.path.join(SEASONS_DIR, filename)

    print("\n================================================")
    print("FILE:", filename)
    print("================================================")

    try:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:

        print("FAILED:", e)
        continue

    print("TYPE:", type(data))

    # ---------------------------------------------------
    # DICT FORMAT
    # ---------------------------------------------------

    if isinstance(data, dict):

        print("TOP LEVEL KEYS:")
        print(list(data.keys())[:50])

        games = data.get("games", [])

        print("GAMES TYPE:", type(games))
        print("GAME COUNT:", len(games))

        if games:

            first = games[0]

            print("\nFIRST GAME KEYS:")
            print(list(first.keys()))

            print("\nFIRST GAME:")
            print(json.dumps(first, indent=2)[:10000])

            break

    # ---------------------------------------------------
    # LIST FORMAT
    # ---------------------------------------------------

    elif isinstance(data, list):

        print("LIST LENGTH:", len(data))

        if data:

            first = data[0]

            print("\nFIRST ITEM TYPE:")
            print(type(first))

            if isinstance(first, dict):

                print("\nFIRST ITEM KEYS:")
                print(list(first.keys()))

            print("\nFIRST ITEM:")
            print(json.dumps(first, indent=2)[:10000])

            break

print("\nDONE")
