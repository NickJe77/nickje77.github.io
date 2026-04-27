import requests
import zipfile
import io
import json
from pathlib import Path

print("IPL 2026 CRICSHEET BUILDER")

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

ZIP_URL = "https://cricsheet.org/downloads/ipl_json.zip"

# -------------------------
# LOAD EXISTING
# -------------------------
existing = []
existing_ids = set()

if OUTPUT.exists():
    with open(OUTPUT) as f:
        existing = json.load(f)
        for m in existing:
            if "file" in m:
                existing_ids.add(m["file"])

print("Existing matches:", len(existing))

# -------------------------
# DOWNLOAD ZIP
# -------------------------
print("Downloading Cricsheet ZIP...")

r = requests.get(ZIP_URL)

if r.status_code != 200:
    print("❌ Failed to download zip")
    exit()

z = zipfile.ZipFile(io.BytesIO(r.content))

files = z.namelist()

print("Files in zip:", len(files))

# -------------------------
# PROCESS MATCHES
# -------------------------
new_matches = []

for file_name in files:

    if not file_name.endswith(".json"):
        continue

    # IPL 2026 filter
    if "2026" not in file_name:
        continue

    short_name = file_name.split("/")[-1]

    if short_name in existing_ids:
        continue

    try:
        data = json.loads(z.read(file_name).decode("utf-8"))

        match = data
        match["file"] = short_name

        new_matches.append(match)
        print("✔ added", short_name)

    except Exception as e:
        print("fail", file_name)

# -------------------------
# MERGE
# -------------------------
combined = existing + new_matches

# optional sort by date
def get_date(m):
    try:
        return m["info"]["dates"][0]
    except:
        return ""

combined.sort(key=get_date)

# -------------------------
# SAVE
# -------------------------
with open(OUTPUT, "w") as f:
    json.dump(combined, f, indent=2)

print("NEW:", len(new_matches))
print("TOTAL:", len(combined))
print("DONE")
