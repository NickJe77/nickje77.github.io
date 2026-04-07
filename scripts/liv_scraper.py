import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("LIV SCRAPER (WIKI FIXED MODE)")

BASE = "https://en.wikipedia.org"
START_YEAR = 2022
END_YEAR = 2026

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}


def clean(x):
    return x.replace("\xa0", " ").strip()


def get_season(year):
    # 🔥 KEY FIX: force simple HTML version
    url = f"{BASE}/wiki/{year}_LIV_Golf_League?printable=yes"
    print(f"\nFetching {year}")

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("FAILED:", r.status_code)
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    tables = soup.find_all("table")
    print("Tables:", len(tables))

    for table in tables:
        text = table.get_text(" ", strip=True).lower()

        if "winner" in text and "location" in text:
            print("FOUND CORRECT TABLE")

            rows = table.find_all("tr")
            events = []

            for row in rows:
                cols = [clean(td.text) for td in row.find_all("td")]

                if len(cols) < 4:
                    continue

                # ✅ fixed mapping
                date = cols[0]
                event = cols[1]
                location = cols[2]
                winner = cols[3]

                score = cols[4] if len(cols) > 4 else ""

                if len(event) < 3:
                    continue

                if "team" in event.lower():
                    continue

                events.append({
                    "season": year,
                    "event": event,
                    "date": date,
                    "location": location,
                    "winner": winner,
                    "score": score
                })

            print(f"{year}: {len(events)} events")
            return events

    print("NO TABLE FOUND")
    return []


# -----------------------
# RUN
# -----------------------
all_events = []

for year in range(START_YEAR, END_YEAR + 1):
    data = get_season(year)

    # always overwrite file
    with open(OUT / f"{year}.json", "w") as f:
        json.dump(data, f, indent=2)

    if data:
        all_events.extend(data)

with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("\nDONE")
