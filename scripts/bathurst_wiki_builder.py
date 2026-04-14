import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (FINAL STABLE)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2003
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})


# -----------------------
# HELPERS
# -----------------------
def clean(v):
    if not v:
        return None
    v = str(v)
    v = re.sub(r"\[[^\]]*\]", "", v)
    v = v.replace("\xa0", " ")
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
# DRIVER FILTER
# -----------------------
def looks_like_driver(text):
    if not text:
        return False

    text = clean(text)
    if not text:
        return False

    words = text.split()
    if len(words) < 2 or len(words) > 4:
        return False

    banned = [
        "racing", "motorsport", "engineering", "team",
        "holden", "ford", "nissan", "commodore", "falcon",
        "mobil", "shell", "castrol", "caltex", "red bull",
        "performance", "supercheap"
    ]

    low = text.lower()
    if any(b in low for b in banned):
        return False

    return True


# -----------------------
# EXTRACT DRIVERS (FIXED)
# -----------------------
def extract_drivers(cell):
    lines = []

    # get clean line-separated text
    for s in cell.stripped_strings:
        s = clean(s)
        if s:
            lines.append(s)

    drivers = []
    seen = set()

    for line in lines:
        if not looks_like_driver(line):
            continue

        key = line.lower()
        if key in seen:
            continue

        drivers.append(line)
        seen.add(key)

        if len(drivers) == 2:
            break

    return drivers


# -----------------------
# FIND RESULTS TABLE (ROBUST)
# -----------------------
def find_results_table(soup):
    best_table = None
    best_headers = None
    best_score = 0

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        for tr in rows[:5]:
            cells = tr.find_all(["th", "td"])
            if len(cells) < 4:
                continue

            headers = [clean(c.get_text()) for c in cells if c]
            header_text = " ".join([h.lower() for h in headers if h])

            score = 0

            if "pos" in header_text:
                score += 2
            if "driver" in header_text:
                score += 3
            if "car" in header_text or "vehicle" in header_text:
                score += 2
            if "team" in header_text or "entrant" in header_text:
                score += 1
            if "laps" in header_text:
                score += 1

            if "pos" not in header_text or "driver" not in header_text:
                continue

            if score > best_score:
                best_score = score
                best_table = table
                best_headers = headers

    return best_table, best_headers


# -----------------------
# SCRAPER
# -----------------------
def scrape_year(year):
    url = "https://en.wikipedia.org/wiki/" + quote(f"{year}_Bathurst_1000")

    html = fetch(url)
    if not html:
        print("  fetch failed")
        return None

    soup = BeautifulSoup(html, "html.parser")

    table, headers = find_results_table(soup)

    if not table:
        print("  no table found")
        return None

    headers = [clean(h) for h in headers]

    try:
        pos_idx = next(i for i, h in enumerate(headers) if h and "pos" in h.lower())
        drivers_idx = next(i for i, h in enumerate(headers) if h and "driver" in h.lower())
    except:
        print("  header mapping failed")
        return None

    car_idx = next(
        (i for i, h in enumerate(headers)
         if h and ("car" in h.lower() or "vehicle" in h.lower())),
        None
    )

    results = []
    started = False

    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if not cells:
            continue

        row_text = " ".join([clean(c.get_text()) or "" for c in cells]).lower()

        if not started:
            if "pos" in row_text and "driver" in row_text:
                started = True
            continue

        if len(cells) <= max(pos_idx, drivers_idx):
            continue

        pos = safe_int(cells[pos_idx].get_text())
        if pos is None:
            continue

        drivers = extract_drivers(cells[drivers_idx])

        constructor = None
        if car_idx is not None and car_idx < len(cells):
            constructor = clean(cells[car_idx].get_text())

        results.append({
            "finish_pos": pos,
            "drivers": drivers,
            "constructor": constructor
        })

    if not results:
        print("  no results parsed")
        return None

    results.sort(key=lambda x: x["finish_pos"])

    return {
        "year": year,
        "results": results,
        "winner": results[0]["drivers"],
        "source": url
    }


# -----------------------
# RUN
# -----------------------
for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    path = SEASONS_DIR / f"{year}.json"

    data = scrape_year(year)

    if not data:
        print("  skipped")
        continue

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"  saved {len(data['results'])} results")

    time.sleep(0.2)

print("\nDONE")
