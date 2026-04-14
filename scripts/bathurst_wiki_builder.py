import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (FINAL STABLE - 2003+ ONLY)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2003  # 🔥 DO NOT TOUCH EARLY YEARS
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

WIKI_BASE = "https://en.wikipedia.org/wiki/"


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
# WIKIPEDIA SCRAPER (ROBUST)
# -----------------------
def scrape_wikipedia(year):
    url = WIKI_BASE + quote(f"{year}_Bathurst_1000")

    html = fetch(url)
    if not html:
        print("  fetch failed")
        return None

    soup = BeautifulSoup(html, "html.parser")

    correct_table = None

    # 🔥 FIND CORRECT RESULTS TABLE
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        headers = [clean(th.get_text()) for th in rows[0].find_all("th")]
        header_text = " ".join([h.lower() for h in headers if h])

        # relaxed but safe
        if "pos" in header_text and "driver" in header_text:
            correct_table = table
            break

    if not correct_table:
        print("  no valid table")
        return None

    rows = correct_table.find_all("tr")

    headers = [clean(th.get_text()) for th in rows[0].find_all("th")]

    try:
        pos_idx = next(i for i, h in enumerate(headers) if "pos" in h.lower())
        drivers_idx = next(i for i, h in enumerate(headers) if "driver" in h.lower())
    except:
        print("  header mapping failed")
        return None

    car_idx = next(
        (i for i, h in enumerate(headers)
         if "car" in h.lower() or "vehicle" in h.lower()),
        None
    )

    results = []

    for tr in rows[1:]:
        tds = tr.find_all("td")

        if not tds or len(tds) <= max(pos_idx, drivers_idx):
            continue

        pos = safe_int(tds[pos_idx].get_text())
        if pos is None:
            continue

        driver_cell = tds[drivers_idx]

        # 🔥 EXTRACT BOTH DRIVERS
        drivers = []

        for a in driver_cell.find_all("a"):
            name = clean(a.get_text())
            if name and " " in name:
                drivers.append(name)

        # fallback if links missing
        if not drivers:
            text = clean(driver_cell.get_text(" ")) or ""
            drivers = re.findall(
                r"[A-Z][A-Za-z'.-]+\s+[A-Z][A-Za-z'.-]+",
                text
            )

        # remove duplicates
        final = []
        seen = set()
        for d in drivers:
            k = d.lower()
            if k not in seen:
                final.append(d)
                seen.add(k)

        constructor = None
        if car_idx is not None and car_idx < len(tds):
            constructor = clean(tds[car_idx].get_text())

        results.append({
            "finish_pos": pos,
            "drivers": final,
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

    # 🔥 SAFE: do NOT overwrite if scrape fails
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
