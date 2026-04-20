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

existing = set((d["year"], d["event"]) for d in data)

print("Existing records:", len(existing))

# -----------------------
# ESPN SCHEDULE (WORKS IN GITHUB)
# -----------------------
URL = "https://www.espn.com/golf/schedule"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(URL, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

tables = soup.select("table")

new_rows = []

for table in tables:
    rows = table.select("tbody tr")

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 2:
            continue

        date = cols[0].text.strip()
        event = cols[1].text.strip()

        # try get winner if exists
        winner = ""
        if len(cols) >= 3:
            winner = cols[2].text.strip()

        year = 2026  # current season

        key = (year, event)

        if key in existing:
            continue

        print("Adding:", event)

        new_rows.append({
            "tour": "pga",
            "year": year,
            "date": date,
            "event": event,
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
if new_rows:
    data.extend(new_rows)

    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("✅ Added", len(new_rows), "events")
else:
    print("No new events found")
