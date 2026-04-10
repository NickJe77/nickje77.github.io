import json
from pathlib import Path

print("BATHURST REBUILD (FIXED + SAFE)")

BASE = Path("docs/data/bathurst")

MAP_FILE = BASE / "driver_map.json"

if MAP_FILE.exists():
    with open(MAP_FILE) as f:
        DRIVER_MAP = json.load(f)
else:
    DRIVER_MAP = {}

# DO NOT TOUCH THESE FILES
files = [
    f for f in BASE.glob("*.json")
    if f.name not in ["driver_map.json", "index.json"]
]

def is_fake(name):
    return str(name).lower().startswith("driver ")

def is_number(val):
    return str(val).isdigit()

for file in files:

    with open(file) as f:
        data = json.load(f)

    changed = False

    for r in data.get("results", []):

        drivers = r.get("drivers")

        if not drivers:
            continue

        if isinstance(drivers, str):
            drivers = [drivers]

        cleaned = []

        for d in drivers:
            d_str = str(d)

            # ❌ REMOVE FAKE PLACEHOLDERS
            if is_fake(d_str):
                continue

            # ⚠️ FIX NUMBERS ONLY IF WE HAVE A REAL MAP
            if is_number(d_str) and d_str in DRIVER_MAP:
                cleaned.extend(DRIVER_MAP[d_str])
                changed = True
            else:
                cleaned.append(d_str)

        if cleaned:
            r["drivers"] = cleaned

    # ✅ ALWAYS REBUILD WINNERS FROM POSITION
    for r in data.get("results", []):
        pos = str(r.get("pos") or r.get("finish") or "").strip()

        if pos == "1":
            data["winners"] = r.get("drivers", [])

    if changed:
        with open(file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✔ updated {file.name}")
    else:
        print(f"– no change {file.name}")

print("DONE")
