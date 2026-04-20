import requests
from bs4 import BeautifulSoup
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

existing_events = set((d["year"], d["event"]) for d in data)

print("Existing records:", len(existing_events))

# -----------------------
# SCRAPE PGA SCHEDULE
# -----------------------
URL = "https://www.pgatour.com/schedule"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(URL, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

events = []

cards = soup.select("div.css-1y0v7zb")  # schedule cards (stable class used for events)

print("Found cards:", len(cards))

for c in cards:

    try:
        name = c.select_one("span.css-1g9p1c6").text.strip()
    except:
        continue

    try:
        date = c.select_one("span.css-1v0q3ez").text.strip()
    except:
        date = ""

    try:
        winner = c.select_one("span.css-1x0e9x2").text.strip()
    except:
        winner = ""

    year = 2026  # keep fixed for now

    key = (year, name)

    if key in existing_events:
        continue

    print("Adding:", name)

    events.append({
        "tour": "pga",
        "year": year,
        "date": date,
        "event": name,
        "winner": winner,
        "major": False,
        "score": "",
        "venue": "",
        "country": "",
        "url": ""
    })

# -----------------------
# SAVE
# -----------------------
if events:
    data.extend(events)

    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("✅ Added", len(events), "new events")
else:
    print("No new events found")
