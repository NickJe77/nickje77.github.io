import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("LIV SCRAPER (FORCED WORKING VERSION)")

BASE = "https://en.wikipedia.org"
START_YEAR = 2022
END_YEAR = 2026

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def clean(x):
    return x.replace("\xa0", " ").strip()


def extract_events(table, year):
    events = []

    rows = table.find_all("tr")

    for row in rows:
        cols = [clean(td.text) for td in row.find_all("td")]

        if len(cols) < 4:
            continue

        # force mapping based on actual LIV structure
        date = cols[0]
        event = cols[1]
        location = cols[2]
        winner = cols[3]

        score = ""
        if len(cols) > 4:
            score = cols[4]

        # skip garbage rows
        if "team" in event.lower():
            continue

        if len(event) < 3:
            continue

        events.append({
            "season": year,
            "event": event,
            "date": date,
            "location": location,
            "winner": winner,
            "score": score
        })

    return events


def get_season(year):
    url = f"{BASE}/wiki/{year}_LIV_Golf_League"
    print(f"\nFetching {year}...")

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("FAILED")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    tables = soup.find_all("table")

    best = None

    # 🔥 find the correct table manually
    for table in tables:
        text = table.get_text(" ", strip=True).lower()

        if "winner" in text and "location" in text and "date" in text:
            best = table
            break

    if not best:
        print("NO TABLE FOUND")
        return []

    events = extract_events(best, year)

    print(f"{year}: {len(events)} events")
    return events


# -----------------------
# RUN
# -----------------------
all_events = []

for year in range(START_YEAR, END_YEAR + 1):
    data = get_season(year)

    if data:
        with open(OUT / f"{year}.json", "w") as f:
            json.dump(data, f, indent=2)

        all_events.extend(data)
    else:
        print(f"{year} EMPTY")

with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("\nDONE")
