import json
from pathlib import Path

print("BUILDING TENNIS EVENTS")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
EVENT_DIR = BASE / "events"

EVENT_DIR.mkdir(parents=True, exist_ok=True)

all_matches = []

# LOAD ALL MATCHES
for file in MATCH_DIR.glob("*.json"):
    data = json.load(open(file))
    all_matches.extend(data["matches"])

print(f"Loaded {len(all_matches)} matches")

events = {}

for m in all_matches:
    season = m.get("season")
    tournament = m.get("tournament", "Unknown Event")

    key = f"{season}_{tournament}"

    if key not in events:
        events[key] = {
            "season": season,
            "tournament": tournament,
            "matches": []
        }

    events[key]["matches"].append(m)

# SAVE EVENTS
for key, event in events.items():
    season = event["season"]

    out_file = EVENT_DIR / f"{season}.json"

    # group multiple events per season
    if out_file.exists():
        existing = json.load(open(out_file))
    else:
        existing = []

    existing.append(event)

    with open(out_file, "w") as f:
        json.dump(existing, f, indent=2)

print(f"Saved {len(events)} events")
