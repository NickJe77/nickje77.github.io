import json
from pathlib import Path

DATA_DIR = Path("docs/data/nrl/matches")

for file in DATA_DIR.glob("*.json"):

    with open(file) as f:
        data = json.load(f)

    seen = set()
    cleaned = []

    for row in data:
        key = (row["match_id"], row["player"])

        if key not in seen:
            seen.add(key)
            cleaned.append(row)

    with open(file, "w") as f:
        json.dump(cleaned, f, indent=2)

print("NRL files checked")
