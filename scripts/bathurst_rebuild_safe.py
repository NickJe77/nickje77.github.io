import json
from pathlib import Path

print("SAFE BATHURST REBUILD (NO OVERWRITE)")

SOURCE = Path("docs/data/bathurst")
OUTPUT = Path("docs/data/bathurst_new")

OUTPUT.mkdir(parents=True, exist_ok=True)

MAP_FILE = SOURCE / "driver_map.json"

if MAP_FILE.exists():
    with open(MAP_FILE) as f:
        DRIVER_MAP = json.load(f)
else:
    DRIVER_MAP = {}

def fix_drivers(drivers):

    if isinstance(drivers, str):
        drivers = [drivers]

    if not isinstance(drivers, list):
        return []

    # ONLY fix if ALL are numbers
    if all(str(d).isdigit() for d in drivers):
        fixed = []
        for d in drivers:
            d = str(d)
            if d in DRIVER_MAP:
                fixed.extend(DRIVER_MAP[d])
            else:
                fixed.append(d)
        return fixed

    return drivers  # leave good data untouched


files = [
    f for f in SOURCE.glob("*.json")
    if f.name not in ["driver_map.json", "index.json"]
]

print(f"Files found: {len(files)}")

for file in files:

    with open(file) as f:
        data = json.load(f)

    for r in data.get("results", []):
        r["drivers"] = fix_drivers(r.get("drivers"))

    # rebuild winners safely
    for r in data.get("results", []):
        if r.get("finish") == 1:
            data["winners"] = r.get("drivers", [])

    out_file = OUTPUT / file.name

    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✔ built {file.name}")

print("DONE — check bathurst_new folder")
