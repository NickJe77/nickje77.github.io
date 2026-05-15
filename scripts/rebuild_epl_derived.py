import os
import json

SEASONS_DIR = "docs/data/epl/seasons"

print("INSPECTING EPL JSON STRUCTURE")

files = sorted([
    f for f in os.listdir(SEASONS_DIR)
    if f.endswith(".json")
])

print("FILES:", len(files))

for filename in files:

    path = os.path.join(SEASONS_DIR, filename)

    print("\n===================================================")
    print("FILE:", filename)
    print("===================================================")

    try:

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:

        print("BAD FILE:", e)
        continue

    print("TOP LEVEL TYPE:", type(data))

    if isinstance(data, dict):

        print("TOP LEVEL KEYS:")
        print(list(data.keys())[:50])

        if "games" in data:

            games = data["games"]

            print("GAMES TYPE:", type(games))
            print("GAME COUNT:", len(games))

            if games:

                print("\nFIRST GAME:")
                print(json.dumps(games[0], indent=2)[:10000])

                break

    elif isinstance(data, list):

        print("LIST LENGTH:", len(data))

        if data:

            print("\nFIRST ITEM TYPE:")
            print(type(data[0]))

            print("\nFIRST ITEM:")
            print(json.dumps(data[0], indent=2)[:10000])

            break

print("\nDONE")
