import json
from pathlib import Path

DATA_DIR = Path("docs/data/nrl/matches")

if not DATA_DIR.exists():
    print("Folder not found:", DATA_DIR)
    exit()

files = list(DATA_DIR.glob("*.json"))

if not files:
    print("No match files found")
    exit()

for file in files:

    with open(file) as f:
        data = json.load(f)

    seen = set()
    cleaned = []

    for row in data:

        match_id = row.get("match_id")
        player = row.get("player")

        key = (match_id, player)

        if key not in seen:
            seen.add(key)
            cleaned.append(row)

    with open(file, "w") as f:
        json.dump(cleaned, f, indent=2)

print("NRL files processed")
