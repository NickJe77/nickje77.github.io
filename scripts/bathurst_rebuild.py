import json
from pathlib import Path

print("BATHURST CLEAN REBUILD (REAL DATA ONLY)")

OUTPUT = Path("docs/data/bathurst")
OUTPUT.mkdir(parents=True, exist_ok=True)

# ⚠️ ONLY REAL DATA HERE
# Replace this with your actual scraper later
REAL_DATA = {
    1978: [
        {
            "finish": 1,
            "drivers": ["Peter Brock", "Jim Richards"],
            "car": "Ford Falcon",
            "laps": 163,
            "time": "6:25:00"
        }
    ]
}

for year, results in REAL_DATA.items():

    data = {
        "year": year,
        "track": "Mount Panorama",
        "results": results
    }

    # winners
    for r in results:
        if r["finish"] == 1:
            data["winners"] = r["drivers"]

    with open(OUTPUT / f"{year}.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"✔ built {year}")

print("DONE")
