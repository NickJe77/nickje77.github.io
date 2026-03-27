import json
from pathlib import Path
import re
import unicodedata

print("BUILDING TENNIS EVENTS (CORRECT FORMAT)")

BASE = Path("docs/data/tennis")
MATCH_DIR = BASE / "matches"
EVENT_DIR = BASE / "events"

EVENT_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------
# HELPERS
# -----------------------------
def slug(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"\s+", "-", text)


def extract_year(date):
    return int(date[:4])


# -----------------------------
# LOAD MATCHES
# -----------------------------
all_matches = []

for file in MATCH_DIR.glob("*.json"):
    data = json.load(open(file))

    if isinstance(data, list):
        matches = data
    elif isinstance(data, dict) and "matches" in data:
        matches = data["matches"]
    else:
        continue

    all_matches.extend(matches)

print(f"Loaded {len(all_matches)} matches")


# -----------------------------
# BUILD EVENTS
# -----------------------------
events = {}

for m in all_matches:
    tournament = m.get("tournament", "Unknown")
    surface = m.get("surface", "Hard")
    date = m.get("date", "")

    if not tournament or not date:
        continue

    year = extract_year(date)

    key = f"{year}_{tournament}"

    if key not in events:
        events[key] = {
            "tournament_id": f"{year}-{slug(tournament)}",
            "name": tournament,
            "surface": surface,
            "draw_size": "32",   # placeholder
            "level": "A",        # placeholder
            "date": date,
            "year": year
        }


# -----------------------------
# SAVE PER YEAR
# -----------------------------
season_events = {}

for e in events.values():
    season_events.setdefault(e["year"], []).append(e)

for year, evts in season_events.items():
    out_file = EVENT_DIR / f"{year}.json"

    with open(out_file, "w") as f:
        json.dump(evts, f, indent=2)

    print(f"Saved {len(evts)} events → {out_file}")
