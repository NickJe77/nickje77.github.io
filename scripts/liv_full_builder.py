import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("LIV BUILDER (WORKING VERSION)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

URL = "https://en.wikipedia.org/wiki/LIV_Golf"

r = requests.get(URL)
soup = BeautifulSoup(r.text, "html.parser")

events = []

# 🔥 grab ALL tables and find ones with LIV events
tables = soup.find_all("table")

for table in tables:
    rows = table.find_all("tr")

    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        text = row.get_text(" ", strip=True)

        # only rows that clearly contain LIV events
        if "LIV Golf" not in text:
            continue

        try:
            event = cols[0].get_text(strip=True)
            date = cols[1].get_text(strip=True)
            location = cols[2].get_text(strip=True)
            winner = cols[3].get_text(strip=True)

            # detect season from date
            season = None
            for y in ["2022", "2023", "2024", "2025", "2026"]:
                if y in date:
                    season = int(y)

            if not season:
                continue

            events.append({
                "season": season,
                "event": event,
                "date": date,
                "location": location,
                "winner": winner,
                "score": ""
            })

        except:
            continue

# remove duplicates
seen = set()
clean = []

for e in events:
    key = (e["season"], e["event"])
    if key in seen:
        continue
    seen.add(key)
    clean.append(e)

# sort
clean.sort(key=lambda x: (x["season"], x["event"]))

# write files
with open(OUT / "all.json", "w") as f:
    json.dump(clean, f, indent=2)

years = {}
for e in clean:
    years.setdefault(e["season"], []).append(e)

for y, data in years.items():
    with open(OUT / f"{y}.json", "w") as f:
        json.dump(data, f, indent=2)

print("DONE — EVENTS:", len(clean))
