import json
from pathlib import Path

print("=== BATHURST DEBUG FIX ===")

BASE = Path("docs/data/bathurst")

print(f"Looking in: {BASE.resolve()}")

files = list(BASE.glob("*.json"))

print(f"Files found: {len(files)}")

if not files:
    print("❌ NO FILES FOUND - WRONG PATH")
    exit()

MAP_FILE = BASE / "driver_map.json"

if not MAP_FILE.exists():
    print("❌ driver_map.json missing")
    exit()

with open(MAP_FILE) as f:
    DRIVER_MAP = json.load(f)

print(f"Driver map entries: {len(DRIVER_MAP)}")

def normalise(drivers):

    if isinstance(drivers, str):
        drivers = [drivers]

    if not isinstance(drivers, list):
        return []

    fixed = []

    for d in drivers:
        d = str(d).strip()

        if d.isdigit():
            if d in DRIVER_MAP:
                print(f"Mapping {d} -> {DRIVER_MAP[d]}")
                fixed.extend(DRIVER_MAP[d])
            else:
                print(f"No map for {d}")
                fixed.append(d)
        else:
            fixed.append(d)

    return fixed

for file in files:

    if file.name == "driver_map.json":
        continue

    print(f"\nProcessing: {file.name}")

    with open(file) as f:
        data = json.load(f)

    changed = False

    for r in data.get("results", []):

        original = r.get("drivers")
        fixed = normalise(original)

        if fixed != original:
            print(f"Updating drivers: {original} -> {fixed}")
            r["drivers"] = fixed
            changed = True

    if changed:
        with open(file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✔ SAVED {file.name}")
    else:
        print("– No changes")

print("\nDONE")
