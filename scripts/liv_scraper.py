import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("LIV GOLF SCRAPER (FIXED + STABLE)")

BASE = "https://en.wikipedia.org"
START_YEAR = 2022
END_YEAR = 2026

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def clean(text):
    return text.replace("\xa0", " ").strip()


def get_column_indexes(headers):
    idx = {}

    for i, h in enumerate(headers):
        h = h.lower()

        if "date" in h:
            idx["date"] = i
        elif "tournament" in h or "event" in h:
            idx["event"] = i
        elif "location" in h or "venue" in h:
            idx["location"] = i
        elif "winner" in h:
            idx["winner"] = i
        elif "score" in h or "to par" in h:
            idx["score"] = i

    return idx


def get_season(year):
    url = f"{BASE}/wiki/{year}_LIV_Golf_League"
    print(f"\nFetching {year}...")

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print(f"FAILED: {year}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    tables = soup.find_all("table", {"class": "wikitable"})

    events = []

    for table in tables:
        header_cells = table.find_all("th")
        headers = [clean(th.text) for th in header_cells]

        header_text = " ".join(headers).lower()

        # only use event results table
        if "winner" not in header_text or "date" not in header_text:
            continue

        col_map = get_column_indexes(headers)

        # must have core fields
        if not all(k in col_map for k in ["date", "event", "location", "winner"]):
            continue

        print(f"Table detected with columns: {col_map}")

        rows = table.find_all("tr")[1:]

        for row in rows:
            cols = [clean(td.text) for td in row.find_all("td")]

            if len(cols) < len(headers):
                continue

            try:
                date = cols[col_map["date"]]
                event = cols[col_map["event"]]
                location = cols[col_map["location"]]
                winner = cols[col_map["winner"]]

                score = ""
                if "score" in col_map and col_map["score"] < len(cols):
                    score = cols[col_map["score"]]

                # skip junk rows
                if not event or "team" in event.lower():
                    continue

                events.append({
                    "season": year,
                    "event": event,
                    "date": date,
                    "location": location,
                    "winner": winner,
                    "score": score
                })

            except Exception as e:
                print("Row error:", e)

    print(f"{year}: {len(events)} events")
    return events


# -------------------------------
# RUN
# -------------------------------
all_events = []

for year in range(START_YEAR, END_YEAR + 1):
    data = get_season(year)

    if data:
        with open(OUT / f"{year}.json", "w") as f:
            json.dump(data, f, indent=2)

        all_events.extend(data)
    else:
        print(f"{year} EMPTY")

# combined file
with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("\nDONE — LIV DATA BUILT")
