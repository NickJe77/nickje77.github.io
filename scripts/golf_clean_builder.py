import json
from collections import defaultdict

INPUT_FILE = "docs/data/golf/pga_winners.json"
OUTPUT_FILE = "docs/data/golf/pga_winners.json"

def is_valid(entry):
    if not entry.get("winner"):
        return False

    w = entry["winner"].lower()

    if "postponed" in w:
        return False
    if "cancelled" in w:
        return False
    if "tbd" in w:
        return False

    return True

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned = []
    seen = set()

    for row in data:
        if not is_valid(row):
            continue

        key = (row.get("event"), row.get("year"))

        if key in seen:
            continue

        seen.add(key)
        cleaned.append(row)

    # sort nicely
    cleaned.sort(key=lambda x: (x.get("event",""), x.get("year",0)))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)

    print(f"Cleaned dataset: {len(data)} -> {len(cleaned)} rows")

if __name__ == "__main__":
    main()
