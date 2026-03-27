import json
from pathlib import Path
import re
import unicodedata

print("BUILDING TENNIS EVENTS (2025+ ONLY — FIXED GROUPING)")

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


def clean_tournament(name):
    if not name:
        return "Unknown"

    name = name.lower()

    # remove round junk
    remove = [" qf", " sf", " f", " r16", " r32", " r64", " r128"]
    for r in remove:
        if name.endswith(r):
            name = name.replace(r, "")

    # remove surface/location junk
    name = name.replace("(australia)", "")
    name = name.replace("(usa)", "")
    name = name.replace("hard", "")
    name = name.replace("clay", "")
    name = name.replace("grass", "")

    return name.strip().title()


# -----------------------------
# LOAD MATCHES (2025+ ONLY)
# -----------------------------
all_matches = []

for file in MATCH_DIR.glob("*.json"):
    try:
        year = int(file.stem)
    except:
        continue

    if year < 2025:
        continue  # 🚫 LOCK OLD DATA

    try:
        data = json.load(open(file))
    except:
        continue

    if isinstance(data, list):
        matches = data
    elif isinstance(data, dict):
        matches = data.get("matches", [])
    else:
        continue

    all_matches.extend(matches)

print(f"Loaded {len(all_matches)} matches")


# -----------------------------
# BUILD EVENTS (GROUP PROPERLY)
# -----------------------------
events = {}

for m in all_matches:
    raw_name = m.get("tournament", "Unknown")
    name = clean_tournament(raw_name)

    surface = m.get("surface", "Hard")
    date = m.get("date", "")

    if not name or not date:
        continue

    year = int(date[:4])

    key = f"{year}_{name}"

    if key not in events:
        events[key] = {
            "tournament_id": f"{year}-{slug(name)}",
            "name": name,
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
