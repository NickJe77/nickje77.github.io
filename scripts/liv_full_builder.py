import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("LIV FULL BUILDER (WIKI TABLE PARSER)")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

URL = "https://en.wikipedia.org/wiki/LIV_Golf"

r = requests.get(URL)
soup = BeautifulSoup(r.text, "html.parser")

tables = soup.find_all("table", {"class": "wikitable"})

events = []

for table in tables:
    rows = table.find_all("tr")

    for row in rows[1:]:
        cols = row.find_all(["td", "th"])

        if len(cols) < 4:
            continue

        try:
            event = cols[0].text.strip()
            date = cols[1].text.strip()
            location = cols[2].text.strip()
            winner = cols[3].text.strip()

            if "LIV Golf" not in event:
                continue

            # extract season from date
            season = None
            for year in ["2022", "2023", "2024", "2025", "2026"]:
                if year in date:
                    season = int(year)

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

# sort
events = sorted(events, key=lambda x: (x["season"], x["event"]))

# write all
with open(OUT / "all.json", "w") as f:
    json.dump(events, f, indent=2)

# split by year
years = {}

for e in events:
    years.setdefault(e["season"], []).append(e)

for y, data in years.items():
    with open(OUT / f"{y}.json", "w") as f:
        json.dump(data, f, indent=2)

print("DONE — EVENTS:", len(events))
