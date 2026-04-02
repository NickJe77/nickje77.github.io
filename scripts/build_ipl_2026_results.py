import json
from pathlib import Path

print("BUILD IPL 2026 RESULTS FILE")

INPUT_FILE = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT_FILE = Path("docs/data/ipl/ipl_2026.json")

if not INPUT_FILE.exists():
    print("❌ FULL file missing")
    exit()

with open(INPUT_FILE) as f:
    data = json.load(f)

matches = data if isinstance(data, list) else [data]

results = []

for match in matches:
    info = match.get("info", {})

    results.append({
        "file": match.get("file", ""),
        "date": info.get("dates", [""])[0],
        "teams": info.get("teams", []),
        "venue": info.get("venue", ""),
        "outcome": info.get("outcome", {})
    })

with open(OUTPUT_FILE, "w") as f:
    json.dump(results, f, indent=2)

print("✅ Saved:", OUTPUT_FILE)
