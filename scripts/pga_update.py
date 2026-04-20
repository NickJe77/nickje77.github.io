import requests
import json
import os

FILE = "docs/data/golf/pga_winners.json"

# -----------------------
# LOAD EXISTING DATA
# -----------------------
if os.path.exists(FILE):
    with open(FILE) as f:
        data = json.load(f)
else:
    data = []

existing = set((d["year"], d["event"]) for d in data)

print("Existing records:", len(existing))

# -----------------------
# PGA TOUR JSON (REAL SOURCE)
# -----------------------
URL = "https://statdata.pgatour.com/r/current/schedule-v2.json"

r = requests.get(URL)
js = r.json()

tournaments = js.get("schedule", [])

print("Tournaments found:", len(tournaments))

new_rows = []

for t in tournaments:

    name = t.get("name", "").strip()
    date = t.get("date", {}).get("startDate", "")
    year = int(date[:4]) if date else 2026

    winner = ""
    if t.get("winner"):
        winner = t["winner"].get("playerName", "")

    key = (year, name)

    if key in existing:
        continue

    print("Adding:", name)

    new_rows.append({
        "tour": "pga",
        "year": year,
        "date": date,
        "event": name,
        "winner": winner,
        "major": False,
        "score": "",
        "venue": t.get("courseName", ""),
        "country": "",
        "url": ""
    })

# -----------------------
# SAVE
# -----------------------
if new_rows:
    data.extend(new_rows)

    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("✅ Added", len(new_rows), "events")
else:
    print("No new events found")
