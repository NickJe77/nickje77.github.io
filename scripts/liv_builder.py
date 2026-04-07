import requests
import json
from pathlib import Path

print("LIV BUILDER (REAL DATA)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

# Data Golf events endpoint
URL = "https://datagolf.com/api/v1/tours/events"

r = requests.get(URL)

if r.status_code != 200:
    print("FAILED TO FETCH")
    exit()

data = r.json()

events = []

for e in data.get("events", []):
    # only LIV events
    if "LIV" not in e.get("tour", ""):
        continue

    try:
        events.append({
            "season": int(e.get("year")),
            "event": e.get("event_name"),
            "date": e.get("start_date"),
            "location": e.get("location"),
            "winner": e.get("winner", ""),
            "score": e.get("winning_score", "")
        })
    except:
        continue

# save master
with open(OUT / "all.json", "w") as f:
    json.dump(events, f, indent=2)

# split by year
years = {}

for e in events:
    years.setdefault(e["season"], []).append(e)

for y, data in years.items():
    with open(OUT / f"{y}.json", "w") as f:
        json.dump(data, f, indent=2)

print("DONE — REAL LIV DATA BUILT")
