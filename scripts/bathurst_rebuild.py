import json
from pathlib import Path

print("BATHURST CLEAN FIX")

BASE = Path("docs/data/bathurst")

files = [
    f for f in BASE.glob("*.json")
    if f.name not in ["driver_map.json", "index.json"]
]

def is_fake(name):
    return str(name).lower().startswith("driver ")

for file in files:

    with open(file) as f:
        data = json.load(f)

    changed = False

    for r in data.get("results", []):

        drivers = r.get("drivers")

        if isinstance(drivers, str):
            drivers = [drivers]

        if not isinstance(drivers, list):
            continue

        # REMOVE ONLY FAKE NAMES
        cleaned = [d for d in drivers if not is_fake(d)]

        if cleaned != drivers and cleaned:
            r["drivers"] = cleaned
            changed = True

    # rebuild winners
    for r in data.get("results", []):
        if r.get("finish") == 1:
            data["winners"] = r.get("drivers", [])

    if changed:
        with open(file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✔ cleaned {file.name}")
    else:
        print(f"– no change {file.name}")

print("DONE")
