import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup

print("LIV SCRAPER (FINAL FIXED VERSION)")

START_YEAR = 2022
END_YEAR = 2026

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)


# -----------------------------------
# GET HTML FROM WIKIPEDIA API
# -----------------------------------
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


# -----------------------------------
# EXTRACT EVENTS (FIXED MAPPING)
# -----------------------------------
def extract_events(html, year):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    for table in tables:
        text = table.get_text(" ", strip=True).lower()

        # find correct table
        if "liv golf" in text and "winner" in text:

            rows = table.find_all("tr")
            events = []

            for row in rows:
                cols = [td.text.strip() for td in row.find_all("td")]

                if len(cols) < 2:
                    continue

                try:
                    # ✅ CORRECT COLUMN ORDER
                    event_name = cols[0]
                    date = cols[1] if len(cols) > 1 else ""
                    location = cols[2] if len(cols) > 2 else ""
                    winner = cols[3] if len(cols) > 3 else ""
                    score = cols[4] if len(cols) > 4 else ""

                    # skip junk rows
                    if "liv golf" not in event_name.lower():
                        continue

                    events.append({
                        "season": year,
                        "event": event_name,
                        "date": date,
                        "location": location,
                        "winner": winner,
                        "score": score
                    })

                except:
                    continue

            if events:
                return events

    return []


# -----------------------------------
# RUN
# -----------------------------------
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


# combined file
with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("\nDONE")
