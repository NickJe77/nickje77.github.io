import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("LIV GOLF SCRAPER STARTED")

BASE = "https://en.wikipedia.org"
START_YEAR = 2022
END_YEAR = 2026

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_season(year):
    url = f"{BASE}/wiki/{year}_LIV_Golf_League"
    print(f"Fetching {year}...")

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print(f"FAILED: {year}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    tables = soup.find_all("table", {"class": "wikitable"})
    events = []

    for table in tables:
        headers = [th.text.strip().lower() for th in table.find_all("th")]

        # find event results table
        if "winner" in " ".join(headers) and "date" in " ".join(headers):

            rows = table.find_all("tr")[1:]

            for row in rows:
                cols = [td.text.strip() for td in row.find_all("td")]

                if len(cols) < 4:
                    continue

                try:
                    event = {
                        "season": year,
                        "event": cols[0],
                        "date": cols[1],
                        "location": cols[2],
                        "winner": cols[3],
                    }

                    # optional fields
                    if len(cols) > 4:
                        event["score"] = cols[4]

                    events.append(event)

                except Exception as e:
                    print("Row error:", e)

    return events


all_events = []

for year in range(START_YEAR, END_YEAR + 1):
    season_events = get_season(year)

    if season_events:
        with open(OUT / f"{year}.json", "w") as f:
            json.dump(season_events, f, indent=2)

        all_events.extend(season_events)
        print(f"{year} saved ({len(season_events)} events)")
    else:
        print(f"{year} EMPTY")

# combined file
with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("DONE")
