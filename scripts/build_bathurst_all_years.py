import json
from pathlib import Path

print("BUILDING BATHURST ALL YEARS (SAFE)")

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# ⚠️ TEMP DATA (structure is correct)
# Replace this later with real scraper
# -------------------------------------------------

ALL_YEARS = [
    {
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
            }
        ]
    },
    {
        "year": 2025,
        "track": "Mount Panorama",
        "laps": 161,
        "results": [
            {
                "finish": 1,
                "grid": 5,
                "drivers": ["Driver A", "Driver B"],
                "car": "Chevrolet Camaro",
                "laps": 161,
                "time": "6:15:10"
            }
        ]
    }
]

# -------------------------------------------------
# BUILD FILES
# -------------------------------------------------

for race in ALL_YEARS:

    year = race["year"]
    file = BASE / f"{year}.json"

    # auto winners
    winners = None
    for r in race["results"]:
        if r["finish"] == 1:
            winners = r["drivers"]

    race["winners"] = winners

    # SAVE (does NOT delete anything else)
    with open(file, "w") as f:
        json.dump(race, f, indent=2)

    print(f"Saved {year}")

print("DONE")
