import json
import os

FILE = "docs/data/golf/pga_winners.json"

if not os.path.exists(FILE):
    print("No winners file found")
    exit()

with open(FILE) as f:
    data = json.load(f)

years = set([d["year"] for d in data])

print("Existing years:", sorted(years))

# --- SAFE: only check for missing recent years ---
target_years = [2024, 2025, 2026]

new_rows = []

for y in target_years:
    if y not in years:
        print(f"Missing year {y} — placeholder added")
        new_rows.append({
            "tour": "pga",
            "year": y,
            "date": "",
            "event": "Season Placeholder",
            "winner": "",
            "major": False,
            "score": "",
            "venue": "",
            "country": "",
            "url": ""
        })

if new_rows:
    data.extend(new_rows)

    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("Updated file")
else:
    print("No updates needed")
