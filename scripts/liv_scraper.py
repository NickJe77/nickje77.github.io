import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("LIV SCRAPER DEBUG MODE")

BASE = "https://en.wikipedia.org"
START_YEAR = 2022
END_YEAR = 2026

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def clean(x):
    return x.replace("\xa0", " ").strip()


def get_season(year):
    url = f"{BASE}/wiki/{year}_LIV_Golf_League"
    print(f"\nFetching {year}: {url}")

    r = requests.get(url, headers=HEADERS)

    print("Status:", r.status_code)

    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    tables = soup.find_all("table")
    print("Tables found:", len(tables))

    for i, table in enumerate(tables):
        text = table.get_text(" ", strip=True).lower()

        if "winner" in text and "date" in text:
            print(f"Using table #{i}")

            rows = table.find_all("tr")
            events = []

            for row in rows:
                cols = [clean(td.text) for td in row.find_all("td")]

                if len(cols) < 4:
                    continue

                print("ROW:", cols[:5])  # 🔥 DEBUG OUTPUT

                event = {
                    "season": year,
                    "date": cols[0],
                    "event": cols[1],
                    "location": cols[2],
                    "winner": cols[3],
                    "score": cols[4] if len(cols) > 4 else ""
                }

                events.append(event)

            print(f"{year} EVENTS:", len(events))
            return events

    print("NO TABLE MATCHED")
    return []


# -----------------------
# RUN
# -----------------------
all_events = []

for year in range(START_YEAR, END_YEAR + 1):
    data = get_season(year)

    # 🔥 FORCE WRITE EVEN IF EMPTY
    with open(OUT / f"{year}.json", "w") as f:
        json.dump(data, f, indent=2)

    if data:
        all_events.extend(data)

# combined file
with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("\nDONE WRITING FILES")
