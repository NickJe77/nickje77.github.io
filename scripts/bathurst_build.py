import json
from pathlib import Path

print("BATHURST FULL REBUILD (WITH DRIVER MAP)")

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

MAP_FILE = BASE / "driver_map.json"

# -----------------------------
# LOAD DRIVER MAP
# -----------------------------
if MAP_FILE.exists():
    with open(MAP_FILE, "r") as f:
        DRIVER_MAP = json.load(f)
else:
    DRIVER_MAP = {}

# -----------------------------
# SAMPLE RAW DATA (REPLACE WITH SCRAPER LATER)
# -----------------------------
# This simulates your scraped input
RAW_DATA = {
    1963: [
        {"finish": 1, "grid": None, "car": "Volkswagen 1200", "number": "54"},
        {"finish": 2, "grid": None, "car": "Morris 850", "number": "55"},
        {"finish": 3, "grid": None, "car": "Volkswagen 1200", "number": "51"}
    ],
    2026: [
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

# -----------------------------
# BUILD FILES
# -----------------------------
for year, results in RAW_DATA.items():

    output = {
        "year": year,
        "track": "Mount Panorama",
        "results": []
    }

    for r in results:

        # 🔥 HANDLE OLD YEARS (number → names)
        if "number" in r:
            num = str(r["number"])
            drivers = DRIVER_MAP.get(num, [num])

        # 🔥 MODERN YEARS (already correct)
        else:
            drivers = r.get("drivers", [])

        entry = {
            "finish": r.get("finish"),
            "grid": r.get("grid"),
            "drivers": drivers,
            "car": r.get("car"),
            "laps": r.get("laps"),
            "time": r.get("time")
        }

        output["results"].append(entry)

    # winners (always first place drivers)
    winners = []
    for r in output["results"]:
        if r["finish"] == 1:
            winners = r["drivers"]

    output["winners"] = winners

    # save
    file_path = BASE / f"{year}.json"
    with open(file_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {year}")

print("DONE")
