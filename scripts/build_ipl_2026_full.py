import requests
import zipfile
import io
import json
from pathlib import Path

print("BUILD IPL 2026 FULL FILE")

URL = "https://cricsheet.org/downloads/ipl_json.zip"

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/zip"
}

print("Downloading IPL data...")

r = requests.get(URL, headers=HEADERS)

# ---- DEBUG ----
print("Status:", r.status_code)
print("Content-Type:", r.headers.get("Content-Type"))

if r.status_code != 200:
    print("❌ Failed request")
    print(r.text[:500])
    exit()

if "zip" not in r.headers.get("Content-Type", ""):
    print("❌ Not a zip file returned")
    print(r.text[:500])
    exit()

# ---- LOAD ZIP SAFELY ----
try:
    z = zipfile.ZipFile(io.BytesIO(r.content))
except zipfile.BadZipFile:
    print("❌ Bad zip file")
    exit()

print("ZIP LOADED")

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

# ---- SAVE ----
with open(OUTPUT, "w") as f:
    json.dump(matches_2026, f)

print("✅ Saved:", OUTPUT)
