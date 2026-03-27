import json
from pathlib import Path

print("BUILDING TENNIS EVENTS")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
EVENT_DIR = BASE / "events"

EVENT_DIR.mkdir(parents=True, exist_ok=True)

all_matches = []

# LOAD ALL MATCH FILES
for file in MATCH_DIR.glob("*.json"):
    data = json.load(open(file))

    # 🔥 HANDLE BOTH STRUCTURES
    if isinstance(data, dict) and "matches" in data:
        all_matches.extend(data["matches"])
    elif isinstance(data, list):
        all_matches.extend(data)
    else:
        print(f"Skipping bad file: {file}")

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

# SAVE EVENTS PER SEASON
season_files = {}

for event in events.values():
    season = event["season"]
    season_files.setdefault(season, []).append(event)

for season, evts in season_files.items():
    out_file = EVENT_DIR / f"{season}.json"

    with open(out_file, "w") as f:
        json.dump(evts, f, indent=2)

    print(f"Saved {len(evts)} events → {out_file}")
