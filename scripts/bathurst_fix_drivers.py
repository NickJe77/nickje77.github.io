import json
from pathlib import Path

print("=== BATHURST DRIVER FIX (FINAL) ===")

BASE = Path("docs/data/bathurst")
MAP_FILE = BASE / "driver_map.json"

# -----------------------------
# CHECK FILES
# -----------------------------
if not BASE.exists():
    print("❌ Folder not found:", BASE)
    exit()

if not MAP_FILE.exists():
    print("❌ driver_map.json missing")
    exit()

# -----------------------------
# LOAD DRIVER MAP
# -----------------------------
with open(MAP_FILE, "r") as f:
    DRIVER_MAP = json.load(f)

print(f"Driver map loaded: {len(DRIVER_MAP)} entries")

# -----------------------------
# GET YEAR FILES ONLY
# -----------------------------
files = [
    f for f in BASE.glob("*.json")
    if f.name not in ["driver_map.json", "index.json"]
]

print(f"Year files found: {len(files)}")

# -----------------------------
# NORMALISE FUNCTION
# -----------------------------
def normalise(drivers):

    # Convert string → list
    if isinstance(drivers, str):
        drivers = [drivers]

    if not isinstance(drivers, list):
        return []

    fixed = []

    for d in drivers:
        if d is None:
            continue

        d = str(d).strip()

        # If numeric → try map
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
total_changes = 0

for file in files:

    print(f"\nProcessing: {file.name}")

    try:
        with open(file, "r") as f:
            data = json.load(f)

        changed = False

        for r in data.get("results", []):

            original = r.get("drivers")
            fixed = normalise(original)

            if fixed != original:
                r["drivers"] = fixed
                changed = True

        # rebuild winners
        winners = []
        for r in data.get("results", []):
            if r.get("finish") == 1:
                winners = r.get("drivers", [])

        data["winners"] = winners

        # SAVE ONLY IF CHANGED
        if changed:
            with open(file, "w") as f:
                json.dump(data, f, indent=2)

            print("✔ UPDATED")
            total_changes += 1
        else:
            print("– No changes")

    except Exception as e:
        print(f"❌ ERROR: {e}")

print(f"\nDONE — Files updated: {total_changes}")
