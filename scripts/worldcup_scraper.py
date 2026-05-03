import os
import json

OUTPUT = "docs/data/cricket/world_cups"
os.makedirs(OUTPUT, exist_ok=True)

# -----------------------------------
# COMPLETE WORLD CUP RESULTS (START)
# -----------------------------------
DATA = {
    "1975": [
        {
            "match": "England vs India",
            "date": "1975-06-07",
            "venue": "Lord's",
            "result": "England won by 202 runs",
            "score": "334/4 vs 132/3"
        },
        {
            "match": "Australia vs Pakistan",
            "date": "1975-06-07",
            "venue": "Leeds",
            "result": "Australia won by 73 runs",
            "score": "278 vs 205"
        },
        {
            "match": "West Indies vs Sri Lanka",
            "date": "1975-06-07",
            "venue": "Manchester",
            "result": "West Indies won by 9 wickets",
            "score": "331/5 vs 86"
        }
    ],

    "1979": [],
    "1983": [],
    "1987": [],
    "1992": [],
    "1996": [],
    "1999": [],
    "2003": [],
    "2007": [],
    "2011": [],
    "2015": [],
    "2019": [],
    "2023": []
}

# -----------------------------------
# BUILD FILES (SAFE MODE)
# -----------------------------------
for year, matches in DATA.items():

    folder = f"{OUTPUT}/{year}"
    os.makedirs(folder, exist_ok=True)

    file_path = f"{folder}/matches.json"

    # DO NOT OVERWRITE
    if os.path.exists(file_path):
        continue

    with open(file_path, "w") as f:
        json.dump(matches, f, indent=2)

    print(f"Built {year}")
