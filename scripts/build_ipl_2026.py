import requests
import zipfile
import io
import json
from pathlib import Path

print("BUILD IPL 2026 (SAFE MODE)")

URL = "https://cricsheet.org/downloads/ipl_json.zip"

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

print("Downloading IPL data...")

r = requests.get(URL, headers=HEADERS)

if r.status_code != 200:
    print("❌ Download failed:", r.status_code)
    exit()

# 🔒 SAFE ZIP LOAD
try:
    z = zipfile.ZipFile(io.BytesIO(r.content))
except:
    print("❌ Not a zip file (blocked or bad download)")
    exit()

matches_2026 = []

for file in z.namelist():
    if not file.endswith(".json"):
        continue

    data = json.loads(z.read(file))
    season = str(data.get("info", {}).get("season"))

    if season == "2026":
        data["file"] = file
        matches_2026.append(data)

print("Matches found:", len(matches_2026))

# 🔥 CRITICAL: DO NOT OVERWRITE GOOD DATA
if not matches_2026:
    print("⚠️ No 2026 data yet — keeping existing file")
    exit()

with open(OUTPUT, "w") as f:
    json.dump(matches_2026, f)

print("✅ Saved:", OUTPUT)
