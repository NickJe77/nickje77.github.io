import json
from pathlib import Path

print("BATHURST DRIVER FIX (BULLETPROOF)")

BASE = Path("docs/data/bathurst")
MAP_FILE = BASE / "driver_map.json"

# -----------------------------
# LOAD DRIVER MAP
# -----------------------------
if not MAP_FILE.exists():
    print("❌ driver_map.json missing")
    exit()

with open(MAP_FILE, "r") as f:
    DRIVER_MAP = json.load(f)

# -----------------------------
# HELPER: NORMALISE DRIVERS
# -----------------------------
def normalise(drivers):

    # Convert string → list
    if isinstance(drivers, str):
        drivers = [drivers]

    if not isinstance(drivers, list):
        return []

    fixed = []

    for d in drivers:

        if not d:
            continue

        d = str(d).strip()

        # If numeric → map it
        if d.isdigit():
            if d in DRIVER_MAP:
                fixed.extend(DRIVER_MAP[d])
            else:
                fixed.append(d)

        else:
            fixed.append(d)

    return fixed

# -----------------------------
# PROCESS FILES
# -----------------------------
files = sorted(BASE.glob("*.json"))

for file in files:

    if file.name == "driver_map.json":
        continue

    try:
        with open(file, "r") as f:
            data = json.load(f)

        changed = False

        for r in data.get("results", []):

            original = r.get("drivers")

            fixed = normalise(original)

            # Only update if changed
            if fixed != original:
                r["drivers"] = fixed
                changed = True

        # rebuild winners
        for r in data.get("results", []):
            if r.get("finish") == 1:
                data["winners"] = r.get("drivers", [])

        # save if needed
        if changed:
            with open(file, "w") as f:
                json.dump(data, f, indent=2)

            print(f"✔ Fixed {file.name}")
        else:
            print(f"– No change {file.name}")

    except Exception as e:
        print(f"⚠ Failed {file.name}: {e}")

print("DONE")
