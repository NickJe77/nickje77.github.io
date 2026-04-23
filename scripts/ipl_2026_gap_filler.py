import requests
import json
from pathlib import Path

print("IPL 2026 GAP FILLER (NEXT_DATA FIX)")

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")

existing = []
existing_ids = set()

if OUTPUT.exists():
    with open(OUTPUT) as f:
        existing = json.load(f)
        for m in existing:
            existing_ids.add(m.get("file"))

print("Existing matches:", len(existing))

url = "https://www.espncricinfo.com/series/ipl-2026-1510719/match-results"

headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(url, headers=headers)

# -------------------------
# EXTRACT NEXT_DATA JSON
# -------------------------
start = r.text.find('__NEXT_DATA__')
if start == -1:
    print("❌ No NEXT_DATA found")
    exit()

start = r.text.find('{', start)
end = r.text.rfind('}') + 1

data = json.loads(r.text[start:end])

# -------------------------
# FIND MATCHES
# -------------------------
matches_data = data["props"]["pageProps"]["data"]["content"]["matches"]

new_matches = []

for m in matches_data:

    match_id = str(m.get("objectId"))
    file_name = f"{match_id}.json"

    if file_name in existing_ids:
        continue

    teams = [t["team"]["name"] for t in m.get("teams", [])]

    match = {
        "meta": {},
        "info": {
            "season": "2026",
            "teams": teams,
            "venue": m.get("ground", {}).get("name", ""),
            "outcome": {"result": m.get("statusText", "")},
            "event": {"name": "Indian Premier League"}
        },
        "innings": [],
        "file": file_name
    }

    new_matches.append(match)
    print("✔ added", match_id)

combined = existing + new_matches

with open(OUTPUT, "w") as f:
    json.dump(combined, f, indent=2)

print("NEW:", len(new_matches))
print("TOTAL:", len(combined))
