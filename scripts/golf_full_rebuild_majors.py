import requests
from bs4 import BeautifulSoup
import json
import re

URL = "https://thegolfnewsnet.com/list-of-mens-golf-major-championship-winners-by-year/"
OUTPUT_FILE = "docs/data/golf/pga_winners.json"

MAJORS = [
    "Masters Tournament",
    "U.S. Open",
    "The Open Championship",
    "PGA Championship"
]

START_YEAR = 1860
END_YEAR = 2026


# -----------------------
# CLEAN NAME (GLOBAL)
# -----------------------
def clean_name(name):
    if not name:
        return ""

    name = name.strip()

    # remove brackets (2), (a), etc
    name = re.sub(r"\s*\(.*?\)", "", name)

    # remove asterisks
    name = name.replace("*", "")

    # convert not played to blank
    if name.lower() in ["not played", "—", "-", ""]:
        return ""

    return name.strip()


# -----------------------
# SCRAPE FULL TABLE
# -----------------------
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
            "Masters Tournament": clean_name(cols[1]),
            "U.S. Open": clean_name(cols[2]),
            "The Open Championship": clean_name(cols[3]),
            "PGA Championship": clean_name(cols[4]),
        }

    return data


# -----------------------
# BUILD FULL DATASET
# -----------------------
def build():
    scraped = scrape()

    final = []
    seen = set()

    for year in range(START_YEAR, END_YEAR + 1):
        year_data = scraped.get(year, {})

        for event in MAJORS:
            key = (event, year)

            if key in seen:
                continue

            seen.add(key)

            winner = year_data.get(event, "")

            final.append({
                "tour": "pga",
                "year": year,
                "event": event,
                "winner": winner,
                "major": True,
                "score": "",
                "venue": "",
                "country": ""
            })

    # sort clean
    final.sort(key=lambda x: (x["event"], x["year"]))

    return final


# -----------------------
# SAVE
# -----------------------
def save(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    data = build()
    save(data)

    print(f"FULL rebuild complete: {len(data)} rows")
