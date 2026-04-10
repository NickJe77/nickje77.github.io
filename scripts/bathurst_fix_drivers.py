import json
from pathlib import Path

print("FIXING BATHURST DRIVER NAMES")

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
# PROCESS ALL YEAR FILES
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

            # If drivers already look correct → skip
            if isinstance(r.get("drivers"), list):
                if all(not d.isdigit() for d in r["drivers"]):
                    continue

            # Fix numeric drivers
            new_drivers = []

            for d in r.get("drivers", []):

                key = str(d)

                if key in DRIVER_MAP:
                    new_drivers.extend(DRIVER_MAP[key])
                    changed = True
                else:
                    new_drivers.append(d)

            r["drivers"] = new_drivers

        # Rebuild winners properly
        winners = []
        for r in data.get("results", []):
            if r.get("finish") == 1:
                winners = r.get("drivers", [])

        data["winners"] = winners

        # Save back
        with open(file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✔ Fixed {file.name}")

    except Exception as e:
        print(f"⚠ Failed {file.name}: {e}")

print("DONE")
