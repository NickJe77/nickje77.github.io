import requests
from bs4 import BeautifulSoup
import json

URL = "https://thegolfnewsnet.com/list-of-mens-golf-major-championship-winners-by-year/"
OUTPUT_FILE = "docs/data/golf/pga_winners.json"

MAJORS = [
    "Masters Tournament",
    "U.S. Open",
    "The Open Championship",
    "PGA Championship"
]

START_YEAR = 1860
END_YEAR = 1967

def load_existing():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def scrape():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table")
    rows = table.find_all("tr")

    data = {}

    for r in rows[1:]:
        cols = [c.get_text(strip=True) for c in r.find_all("td")]

        if len(cols) < 5:
            continue

        year = cols[0]
        if not year.isdigit():
            continue

        year = int(year)

        data[year] = {
            "Masters Tournament": cols[1],
            "U.S. Open": cols[2],
            "The Open Championship": cols[3],
            "PGA Championship": cols[4],
        }

    return data

def clean_name(name):
    if not name:
        return ""

    name = name.replace("*", "").strip()

    if name.lower() in ["—", "-", ""]:
        return ""

    return name

def main():
    existing = load_existing()
    existing_keys = set((e["event"], e["year"]) for e in existing)

    scraped = scrape()

    new_rows = []

    for year in range(START_YEAR, END_YEAR + 1):

        year_data = scraped.get(year, {})

        for event in MAJORS:

            key = (event, year)

            if key in existing_keys:
                continue

            winner = clean_name(year_data.get(event, ""))

            new_rows.append({
                "tour": "pga",
                "year": year,
                "event": event,
                "winner": winner,
                "major": True,
                "score": "",
                "venue": "",
                "country": ""
            })

    combined = existing + new_rows
    combined.sort(key=lambda x: (x.get("event",""), x.get("year",0)))

    save(combined)

    print(f"Added {len(new_rows)} rows (including blanks where needed)")

if __name__ == "__main__":
    main()
