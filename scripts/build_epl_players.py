import os
import json

MATCHES_DIR = "docs/data/epl/matches"

print("DEBUGGING MATCH FILES")

found = False

for root, dirs, files in os.walk(MATCHES_DIR):

    for file in sorted(files):

        if not file.endswith(".json"):
            continue

        path = os.path.join(root, file)

        print(f"\nREADING: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(e)
            continue

        print("\nTYPE:")
        print(type(data))

        if isinstance(data, dict):

            print("\nTOP LEVEL KEYS:")
            print(list(data.keys())[:200])

            print("\nFULL SAMPLE:")
            print(json.dumps(data, indent=2)[:20000])

            found = True
            break

        elif isinstance(data, list):

            print(f"\nLIST LENGTH: {len(data)}")

            if data:

                item = data[0]

                print("\nITEM KEYS:")
                print(list(item.keys())[:200])

                print("\nFULL SAMPLE ITEM:")
                print(json.dumps(item, indent=2)[:20000])

                found = True
                break

    if found:
        break

print("\nDONE")
