import requests
import zipfile
import io
import json
from pathlib import Path

print("BUILD IPL 2026 FROM CRICSHEET")

URL = "https://cricsheet.org/downloads/ipl_json.zip"

OUTPUT = Path("docs/data/ipl/ipl_2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

r = requests.get(URL)
z = zipfile.ZipFile(io.BytesIO(r.content))

matches_2026 = []

for file in z.namelist():
    if not file.endswith(".json"):
        continue

    data = json.loads(z.read(file))

    season = str(data.get("info", {}).get("season"))

    if season != "2026":
        continue

    info = data["info"]

    match = {
        "match_id": file.replace(".json",""),
        "date": info.get("dates", [""])[0],
        "teams": info.get("teams", []),
        "venue": info.get("venue",""),
        "result": info.get("outcome", {}),
    }

    matches_2026.append(match)

print("Matches found:", len(matches_2026))

with open(OUTPUT, "w") as f:
    json.dump(matches_2026, f, indent=2)

print("DONE")
