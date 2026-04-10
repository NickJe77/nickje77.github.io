import json
from pathlib import Path

print("BUILDING BATHURST 2026 (SAFE)")

OUTPUT = Path("docs/data/bathurst/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# ⚠️ TEMP DATA (REPLACE WITH SCRAPER LATER)
# This is structured CORRECTLY for Bathurst
# -------------------------------------------------

race = {
    "year": 2026,
    "track": "Mount Panorama",
    "laps": 161,

    "results": [
        {
            "finish": 1,
            "grid": 3,
            "drivers": ["Driver One", "Driver Two"],
            "car": "Ford Mustang",
            "laps": 161,
            "time": "6:12:34"
        },
        {
            "finish": 2,
            "grid": 1,
            "drivers": ["Driver Three", "Driver Four"],
            "car": "Chevrolet Camaro",
            "laps": 161,
            "time": "+5.3s"
        }
    ]
}

# -------------------------------------------------
# AUTO-GENERATE WINNERS (CRITICAL FIX)
# -------------------------------------------------

winners = None

for r in race["results"]:
    if r["finish"] == 1:
        winners = r["drivers"]

race["winners"] = winners

# -------------------------------------------------
# SAVE
# -------------------------------------------------

with open(OUTPUT, "w") as f:
    json.dump(race, f, indent=2)

print(f"Saved -> {OUTPUT}")
