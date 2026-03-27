import json
from pathlib import Path
import re
import unicodedata

print("BUILDING TENNIS EVENTS (2025+ ONLY)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
EVENT_DIR = BASE / "events"

EVENT_DIR.mkdir(parents=True, exist_ok=True)


def slug(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"\s+", "-", text)


all_matches = []

# 🔥 ONLY LOAD 2025+
for file in MATCH_DIR.glob("*.json"):
    try:
        year = int(file.stem)
    except:
        continue

    if year < 2025:
        continue  # 🚫 LOCK OLD DATA

    data = json.load(open(file))

    if isinstance(data, list):
        matches = data
    elif isinstance(data, dict):
        matches = data.get("matches", [])
    else:
        continue

    all_matches.extend(matches)

print(f"Loaded {len(all_matches)} matches")


events = {}

for m in all_matches:
    tournament = m.get("tournament", "Unknown")
    surface = m.get("surface", "Hard")
    date = m.get("date", "")

    if not tournament or not date:
        continue

    year = int(date[:4])

    key = f"{year}_{tournament}"

    if key not in events:
        events[key] = {
            "tournament_id": f"{year}-{slug(tournament)}",
            "name": tournament,
            "surface": surface,
            "draw_size": "32",
            "level": "A",
            "date": date,
            "year": year
        }


season_events = {}

for e in events.values():
    season_events.setdefault(e["year"], []).append(e)


for year, evts in season_events.items():
    out_file = EVENT_DIR / f"{year}.json"

    with open(out_file, "w") as f:
        json.dump(evts, f, indent=2)

    print(f"Saved {len(evts)} events → {out_file}")
