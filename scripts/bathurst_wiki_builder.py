import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (ROWSPAN FIX FINAL)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2003
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})


def clean(v):
    if not v:
        return None
    v = str(v)
    v = re.sub(r"\[[^\]]*\]", "", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v


def safe_int(v):
    if not v:
        return None
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else None


def fetch(url):
    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return None
        return r.text
    except:
        return None


# -----------------------
# FIND RESULTS TABLE
# -----------------------
def find_table(soup):
    for table in soup.find_all("table"):
        text = table.get_text(" ").lower()
        if "pos" in text and "driver" in text:
            return table
    return None


# -----------------------
# EXTRACT DRIVER FROM CELL
# -----------------------
def extract_driver(cell):
    text = cell.get_text(" ", strip=True)
    text = clean(text)

    if not text:
        return None

    # remove junk
    if any(x in text.lower() for x in [
        "racing", "team", "holden", "ford",
        "commodore", "falcon"
    ]):
        return None

    if len(text.split()) < 2:
        return None

    return text


# -----------------------
# SCRAPE YEAR
# -----------------------
def scrape_year(year):
    url = "https://en.wikipedia.org/wiki/" + quote(f"{year}_Bathurst_1000")

    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    table = find_table(soup)
    if not table:
        print("  no table")
        return None

    results = []
    current = None

    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue

        pos = safe_int(cells[0].get_text())

        # NEW RESULT ROW
        if pos:
            # save previous
            if current:
                results.append(current)

            current = {
                "finish_pos": pos,
                "drivers": [],
                "constructor": None
            }

            # driver
            if len(cells) > 3:
                d = extract_driver(cells[3])
                if d:
                    current["drivers"].append(d)

            # constructor
            if len(cells) > 4:
                current["constructor"] = clean(cells[4].get_text())

        else:
            # CONTINUATION ROW (SECOND DRIVER)
            if current and len(cells) > 3:
                d = extract_driver(cells[3])
                if d:
                    current["drivers"].append(d)

    # add last
    if current:
        results.append(current)

    return {
        "year": year,
        "results": results,
        "winner": results[0]["drivers"] if results else [],
        "source": url
    }


# -----------------------
# RUN
# -----------------------
for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    file_path = SEASONS_DIR / f"{year}.json"

    data = scrape_year(year)

    if not data:
        print("FAILED")
        continue

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"saved {len(data['results'])}")

    time.sleep(0.2)

print("\nDONE")
