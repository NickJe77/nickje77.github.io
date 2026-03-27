import json
from pathlib import Path
import re
import unicodedata

print("BUILDING TENNIS EVENTS (2025+ ONLY — HARD FIX)")

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


def extract_tournament(name):
    if not name:
        return "Unknown"

    name = name.lower()

    # remove brackets
    name = re.sub(r"\(.*?\)", "", name)

    # remove numbers
    name = re.sub(r"\d+", "", name)

    # remove junk words
    junk = [
        "qf", "sf", "f", "r16", "r32", "r64", "r128",
        "round", "final", "qualifying",
        "court", "atp", "men", "singles",
        "hard", "clay", "grass"
    ]

    for j in junk:
        name = name.replace(j, "")

    # collapse spaces
    name = re.sub(r"\s+", " ", name).strip()

    if not name:
        return "Unknown"

    # 🔥 TAKE FIRST 2 WORDS MAX (THIS IS THE KEY FIX)
    parts = name.split()
    if len(parts) >= 2:
        name = f"{parts[0]} {parts[1]}"
    else:
        name = parts[0]

    return name.title()


# -----------------------------
# LOAD MATCHES (LOCK OLD DATA)
# -----------------------------
all_matches = []

for file in MATCH_DIR.glob("*.json"):
    try:
        year = int(file.stem)
    except:
        continue

    if year < 2025:
        continue

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
# BUILD EVENTS
# -----------------------------
events = {}

for m in all_matches:
    raw = m.get("tournament", "")
    name = extract_tournament(raw)

    surface = m.get("surface", "Hard")
    date = m.get("date", "")

    if not name or not date:
        continue

    year = int(date[:4])

    key = f"{year}_{slug(name)}"

    if key not in events:
        events[key] = {
            "tournament_id": key,
            "name": name,
            "surface": surface,
            "draw_size": "32",
            "level": "A",
            "date": date,
            "year": year
        }


# -----------------------------
# SAVE
# -----------------------------
season_events = {}

for e in events.values():
    season_events.setdefault(e["year"], []).append(e)


for year, evts in season_events.items():
    out_file = EVENT_DIR / f"{year}.json"

    with open(out_file, "w") as f:
        json.dump(evts, f, indent=2)

    print(f"Saved {len(evts)} events → {out_file}")
