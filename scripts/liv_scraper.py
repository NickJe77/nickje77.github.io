import requests
import json
from pathlib import Path

print("LIV SCRAPER (WIKI API VERSION)")

START_YEAR = 2022
END_YEAR = 2026

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)


def get_page(year):
    title = f"{year} LIV Golf League"

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text"
    }

    r = requests.get(url, params=params)

    if r.status_code != 200:
        print("FAILED:", year)
        return ""

    data = r.json()

    try:
        return data["parse"]["text"]["*"]
    except:
        print("NO PAGE:", year)
        return ""


def extract_events(html, year):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    events = []

    for table in tables:
        text = table.get_text(" ", strip=True).lower()

        if "winner" in text and "location" in text:

            rows = table.find_all("tr")

            for row in rows:
                cols = [td.text.strip() for td in row.find_all("td")]

                if len(cols) < 4:
                    continue

                event = {
                    "season": year,
                    "date": cols[0],
                    "event": cols[1],
                    "location": cols[2],
                    "winner": cols[3],
                    "score": cols[4] if len(cols) > 4 else ""
                }

                # clean junk
                if len(event["event"]) < 3:
                    continue

                if "team" in event["event"].lower():
                    continue

                events.append(event)

            return events

    return []


# -----------------------
# RUN
# -----------------------
all_events = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\nProcessing {year}")

    html = get_page(year)

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
