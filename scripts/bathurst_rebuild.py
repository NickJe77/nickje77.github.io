import json
from pathlib import Path

print("BATHURST REBUILD (WINNERS ONLY — CLEAN)")

OUT = Path("docs/data/bathurst")
OUT.mkdir(parents=True, exist_ok=True)

# ✅ REAL DATA (starter set — expand later)
DATA = {
    1978: {
        "winners": ["Peter Brock", "Jim Richards"],
        "car": "Ford Falcon",
        "laps": 163
    },
    1979: {
        "winners": ["Peter Brock", "Jim Richards"],
        "car": "Ford Falcon",
        "laps": 163
    },
    1980: {
        "winners": ["Dick Johnson", "John French"],
        "car": "Ford Falcon",
        "laps": 163
    }
}

for year, info in DATA.items():

    race = {
        "year": year,
        "track": "Mount Panorama",
        "results": [
            {
                "finish": 1,
                "drivers": info["winners"],
                "car": info["car"],
                "laps": info["laps"]
            }
        ],
        "winners": info["winners"]
    }

    with open(OUT / f"{year}.json", "w") as f:
        json.dump(race, f, indent=2)

    print(f"✔ built {year}")

print("DONE")
