import json
from pathlib import Path

print("LIV BUILDER START")

BASE = Path("docs/data/golf/liv")
BASE.mkdir(parents=True, exist_ok=True)

MASTER = BASE / "events.json"

if not MASTER.exists():
    print("events.json NOT FOUND")
    exit()

with open(MASTER) as f:
    events = json.load(f)

by_year = {}

for e in events:
    year = e["season"]
    by_year.setdefault(year, []).append(e)

# write per year
for year, data in by_year.items():
    with open(BASE / f"{year}.json", "w") as f:
        json.dump(data, f, indent=2)

# write combined
with open(BASE / "all.json", "w") as f:
    json.dump(events, f, indent=2)

print("DONE — LIV BUILT")
