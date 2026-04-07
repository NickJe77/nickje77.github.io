import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup

print("LIV SCRAPER (FINAL WORKING VERSION)")

START_YEAR = 2022
END_YEAR = 2026

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)


def get_html(year):
    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "parse",
        "page": f"{year} LIV Golf League",
        "format": "json",
        "prop": "text"
    }

    r = requests.get(url, params=params)

    try:
        return r.json()["parse"]["text"]["*"]
    except:
        return ""


def extract_events(html, year):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    for table in tables:
        text = table.get_text(" ", strip=True).lower()

        # 🔥 smarter detection
        if "liv golf" in text and "winner" in text:

            rows = table.find_all("tr")
            events = []

            for row in rows:
                cols = [td.text.strip() for td in row.find_all("td")]

                if len(cols) < 4:
                    continue

                try:
                    event = {
                        "season": year,
                        "date": cols[0],
                        "event": cols[1],
                        "location": cols[2],
                        "winner": cols[3],
                        "score": cols[4] if len(cols) > 4 else ""
                    }

                    # clean junk rows
                    if len(event["event"]) < 5:
                        continue

                    if "team" in event["event"].lower():
                        continue

                    events.append(event)

                except:
                    continue

            if events:
                return events

    return []


# -----------------------
# RUN
# -----------------------
all_events = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\nProcessing {year}")

    html = get_html(year)

    if not html:
        data = []
    else:
        data = extract_events(html, year)

    print(f"{year}: {len(data)} events")

    with open(OUT / f"{year}.json", "w") as f:
        json.dump(data, f, indent=2)

    if data:
        all_events.extend(data)

with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("\nDONE")
