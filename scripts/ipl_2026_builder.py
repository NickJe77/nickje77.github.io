import requests
import json
import time
from pathlib import Path

print("IPL 2026 BUILDER (ESPN FIXED)")

OUTPUT = Path("docs/data/ipl/seasons/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# 🔑 HEADERS FIX (this is what broke your old scraper)
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.espncricinfo.com/",
    "Origin": "https://www.espncricinfo.com"
}

session = requests.Session()
session.headers.update(HEADERS)

# 🔢 IPL 2026 MATCH IDS (same structure as before)
MATCH_IDS = list(range(70343128, 70343225))

matches = []

for match_id in MATCH_IDS:
    try:
        url = f"https://site.web.api.espn.com/apis/v2/sports/cricket/ipl/scoreboard?event={match_id}"

        r = session.get(url, timeout=10)

        print("ID:", match_id, "STATUS:", r.status_code, "LEN:", len(r.text))

        if r.status_code != 200 or len(r.text) < 500:
            continue

        data = r.json()

        if not data.get("events"):
            continue

        event = data["events"][0]
        comp = event["competitions"][0]
        teams = comp["competitors"]

        match = {
            "match_id": match_id,
            "date": event.get("date", ""),
            "status": comp.get("status", {}).get("type", {}).get("description", ""),
            "venue": comp.get("venue", {}).get("fullName", ""),
            "teams": [
                teams[0]["team"]["displayName"],
                teams[1]["team"]["displayName"]
            ],
            "scores": [
                teams[0].get("score", ""),
                teams[1].get("score", "")
            ]
        }

        matches.append(match)
        print("✔ added", match_id)

        time.sleep(1)

    except Exception as e:
        print("❌ fail", match_id, e)

# 💾 SAVE
out = {
    "season": "2026",
    "matches": matches
}

with open(OUTPUT, "w") as f:
    json.dump(out, f, indent=2)

print("DONE:", len(matches), "matches")
