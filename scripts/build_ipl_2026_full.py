import requests
import zipfile
import io
import json
from pathlib import Path

print("BUILD IPL 2026 FULL FILE")

URL = "https://cricsheet.org/downloads/ipl_json.zip"

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

print("Downloading IPL data...")

r = requests.get(URL)
z = zipfile.ZipFile(io.BytesIO(r.content))

matches_2026 = []

for file in z.namelist():
    if not file.endswith(".json"):
        continue

    data = json.loads(z.read(file))

    season = data.get("info", {}).get("season")

    if str(season) == "2026":
        matches_2026.append(data)

print("Matches found:", len(matches_2026))

if not matches_2026:
    print("❌ No 2026 matches yet (season may not be in Cricsheet)")
    exit()

with open(OUTPUT, "w") as f:
    json.dump(matches_2026, f)

print("✅ Saved:", OUTPUT)
