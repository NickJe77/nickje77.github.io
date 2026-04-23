import requests
import json
from pathlib import Path

print("IPL 2026 WORKING DATA PULL")

OUTPUT = Path("docs/data/ipl/seasons/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

url = "https://hsapi.espncricinfo.com/v1/pages/series/home?seriesId=1510719"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(url, headers=headers)

print("STATUS:", r.status_code)
print("LEN:", len(r.text))

data = r.json()

matches = []

for block in data.get("content", []):
    if "matches" in block:
        for m in block["matches"]:
            match = {
                "match_id": m.get("objectId"),
                "teams": [
                    m.get("teams", [{}])[0].get("team", {}).get("name", ""),
                    m.get("teams", [{}])[1].get("team", {}).get("name", "")
                ],
                "date": m.get("startDate"),
                "status": m.get("statusText")
            }
            matches.append(match)

with open(OUTPUT, "w") as f:
    json.dump({"season": "2026", "matches": matches}, f, indent=2)

print("DONE:", len(matches))
