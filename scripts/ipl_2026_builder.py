import requests
import zipfile
import io
import json
from pathlib import Path

print("IPL 2026 BUILDER (CRICSHEET - STABLE)")

URL = "https://cricsheet.org/downloads/ipl_json.zip"

OUTPUT = Path("docs/data/ipl/seasons/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

r = requests.get(URL)
z = zipfile.ZipFile(io.BytesIO(r.content))

matches = []

for file in z.namelist():
    if not file.endswith(".json"):
        continue

    data = json.loads(z.read(file))

    info = data.get("info", {})
    season = str(info.get("season"))

    if season != "2026":
        continue

    match = {
        "match_id": file.replace(".json",""),
        "date": info.get("dates", [""])[0],
        "teams": info.get("teams", []),
        "venue": info.get("venue",""),
        "result": info.get("outcome", {}),
    }

    matches.append(match)

print("MATCHES FOUND:", len(matches))

with open(OUTPUT, "w") as f:
    json.dump({
        "season": "2026",
        "matches": matches
    }, f, indent=2)

print("DONE")
