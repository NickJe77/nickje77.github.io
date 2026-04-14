import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (STABLE FINAL - NO CRASH)")

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
    if v is None:
        return None
    v = str(v)
    v = re.sub(r"\[[^\]]*\]", "", v)
    v = v.replace("\xa0", " ")
    v = re.sub(r"\s+", " ", v).strip()
    return v if v else None


def safe_int(v):
    if v is None:
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
# FIND TABLE (SAFE)
# -----------------------
def find_results_table(soup):
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        for tr in rows[:3]:
            cells = tr.find_all(["th", "td"])
            headers = [clean(c.get_text()) for c in cells]
            header_text = " ".join([h.lower() for h in headers if h])

            # relaxed match
            if "pos" in header_text and "driver" in header_text:
                return table, headers

    return None, None


# -----------------------
# DRIVER EXTRACTION
# -----------------------
def extract_drivers(cell):
    drivers = []

    for a in cell.find_all("a"):
        name = clean(a.get_text())
        if name and " " in name:
            drivers.append(name)

    # fallback
    if not drivers:
        text = clean(cell.get_text(" ")) or ""
        drivers = re.findall(
            r"[A-Z][A-Za-z'.-]+\s+[A-Z][A-Za-z'.-]+",
            text
        )

    # dedupe
    seen = set()
    out = []
    for d in drivers:
        k = d.lower()
        if k not in seen:
            out.append(d)
            seen.add(k)

    return out


# -----------------------
# SCRAPER
# -----------------------
def scrape_wikipedia(year):
    url = "https://en.wikipedia.org/wiki/" + quote(f"{year}_Bathurst_1000")

    html = fetch(url)
    if not html:
        print("  fetch failed")
        return None

    soup = BeautifulSoup(html, "html.parser")

    table, headers = find_results_table(soup)

    if table is None:
        print("  no table found")
        return None

    rows = table.find_all("tr")

    headers = [clean(h) for h in headers]

    # column indexes (safe)
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

    for tr in rows:
        cells = tr.find_all(["th", "td"])  # 🔥 FIX (IMPORTANT)
        if not cells:
            continue

        text = " ".join([clean(c.get_text()) or "" for c in cells]).lower()

        # find header row start
        if not started:
            if "pos" in text and "driver" in text:
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
index = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    file_path = SEASONS_DIR / f"{year}.json"

    data = scrape_wikipedia(year)

    if not data:
        print("  skipped (kept existing)")
        if file_path.exists():
            index.append({
                "year": year,
                "file": f"/data/bathurst/seasons/{year}.json"
            })
        continue

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    index.append({
        "year": year,
        "file": f"/data/bathurst/seasons/{year}.json"
    })

    print(f"  saved {len(data['results'])} results")

    time.sleep(0.2)


with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("\nDONE")
