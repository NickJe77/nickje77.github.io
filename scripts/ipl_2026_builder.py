import requests
import json
from pathlib import Path

print("IPL 2026 BUILDER (FIXED MATCH DISCOVERY)")

OUTPUT = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# -------------------------
# LOAD EXISTING DATA (SAFE)
# -------------------------
existing = []
existing_ids = set()

if OUTPUT.exists():
    with open(OUTPUT) as f:
        existing = json.load(f)
        for m in existing:
            existing_ids.add(m.get("file"))

print("Existing matches:", len(existing))

# -------------------------
# STEP 1: GET MATCH LIST (WORKING ENDPOINT)
# -------------------------
url = "https://site.web.api.espn.com/apis/site/v2/sports/cricket/ipl/scoreboard"

r = requests.get(url, headers=HEADERS)

print("STATUS:", r.status_code)

if r.status_code != 200:
    print("❌ scoreboard endpoint failed")
    exit()

data = r.json()

events = data.get("events", [])

print("Events found:", len(events))

match_ids = []

for e in events:
    match_ids.append(str(e.get("id")))

print("Match IDs:", match_ids)

# -------------------------
# STEP 2: BUILD MATCHES (KEEP YOUR FORMAT)
# -------------------------
new_matches = []

for match_id in match_ids:

    file_name = f"{match_id}.json"

    if file_name in existing_ids:
        continue

    try:
        event = next(e for e in events if e.get("id") == match_id)

        comp = event["competitions"][0]
        teams = comp["competitors"]

        match = {
            "meta": {},
            "info": {
                "season": "2026",
                "teams": [
                    teams[0]["team"]["displayName"],
                    teams[1]["team"]["displayName"]
                ],
                "venue": comp.get("venue", {}).get("fullName", ""),
                "outcome": {"result": comp.get("status", {}).get("type", {}).get("description", "")},
                "event": {"name": "Indian Premier League"}
            },
            "innings": [],
            "file": file_name
        }

        new_matches.append(match)
        print("✔ added", match_id)

    except Exception as e:
        print("fail", match_id)

# -------------------------
# STEP 3: MERGE + SAVE
# -------------------------
combined = existing + new_matches

with open(OUTPUT, "w") as f:
    json.dump(combined, f, indent=2)

print("NEW:", len(new_matches))
print("TOTAL:", len(combined))
print("DONE")
