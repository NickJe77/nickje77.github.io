import requests
import zipfile
import io
import json
from pathlib import Path

print("IPL 2026 SAFE BUILDER (MERGE MODE)")

URL = "https://cricsheet.org/downloads/ipl_json.zip"

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# -------------------------
# LOAD EXISTING DATA
# -------------------------
existing = []

if OUTPUT.exists():
    with open(OUTPUT) as f:
        existing = json.load(f)

existing_ids = {m.get("file") for m in existing}

print("Existing matches:", len(existing))

# -------------------------
# DOWNLOAD ZIP
# -------------------------
r = requests.get(URL)
z = zipfile.ZipFile(io.BytesIO(r.content))

new_matches = []

for file in z.namelist():
    if not file.endswith(".json"):
        continue

    data = json.loads(z.read(file))

    season = str(data.get("info", {}).get("season"))

    if season != "2026":
        continue

    if file in existing_ids:
        continue  # skip already stored

    data["file"] = file
    new_matches.append(data)

# -------------------------
# MERGE
# -------------------------
combined = existing + new_matches

print("New matches added:", len(new_matches))
print("Total matches:", len(combined))

# -------------------------
# SAVE
# -------------------------
with open(OUTPUT, "w") as f:
    json.dump(combined, f, indent=2)

print("DONE")
