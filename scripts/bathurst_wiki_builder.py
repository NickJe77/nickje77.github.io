import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (HEADER-LOCKED FIX)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1963
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

WIKI_BASE = "https://en.wikipedia.org/wiki/"


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


def split_early_drivers(text):
    text = clean(text)
    if not text:
        return []

    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace(" and ", "/")
    text = text.replace("&", "/")

    parts = [clean(x) for x in re.split(r"\s*/\s*", text) if clean(x)]
    return parts if parts else [text]


# -----------------------
# UNIQUECARS (1963–2002)
# -----------------------
def scrape_uniquecars(year):
    url = f"https://www.uniquecarsandparts.com/bathurst_{year}.htm"
    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    best = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        results = []

        for tr in rows:
            cols = [clean(td.get_text()) for td in tr.find_all("td")]
            cols = [x for x in cols if x]

            if len(cols) < 3:
                continue

            pos = safe_int(cols[0])
            if pos is None:
                continue

            results.append({
                "finish_pos": pos,
                "drivers": split_early_drivers(cols[1]),
                "constructor": cols[2]
            })

        if len(results) > len(best):
            best = results

    if not best:
        return None

    best.sort(key=lambda x: x["finish_pos"])

    return {
        "year": year,
        "results": best,
        "winner": best[0]["drivers"],
        "source": url
    }


# -----------------------
# WIKIPEDIA (REAL FIX)
# -----------------------
def scrape_wikipedia(year):
    url = WIKI_BASE + quote(f"{year}_Bathurst_1000")

    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # 🔥 STEP 1: FIND "Race results" HEADER
    header = None
    for h in soup.find_all(["h2", "h3"]):
        if "race results" in h.get_text(" ").lower():
            header = h
            break

    if not header:
        return None

    # 🔥 STEP 2: GET FIRST TABLE AFTER HEADER
    table = header.find_next("table")
    if not table:
        return None

    rows = table.find_all("tr")
    if len(rows) < 5:
        return None

    # 🔥 STEP 3: FIND COLUMN INDEXES
    headers = [clean(th.get_text()) for th in rows[0].find_all("th")]

    pos_idx = None
    drivers_idx = None
    car_idx = None

    for i, h in enumerate(headers):
        h_low = (h or "").lower()

        if "pos" in h_low:
            pos_idx = i
        elif "driver" in h_low:
            drivers_idx = i
        elif "car" in h_low:
            car_idx = i

    if pos_idx is None or drivers_idx is None:
        return None

    results = []

    # 🔥 STEP 4: READ ROWS
    for tr in rows[1:]:
        tds = tr.find_all("td")
        if len(tds) <= max(pos_idx, drivers_idx):
            continue

        pos = safe_int(tds[pos_idx].get_text())
        if pos is None:
            continue

        driver_cell = tds[drivers_idx]

        # 🔥 THIS IS THE KEY FIX
        drivers = []
        for a in driver_cell.find_all("a"):
            name = clean(a.get_text())
            if name and " " in name:
                drivers.append(name)

        if not drivers:
            text = clean(driver_cell.get_text(" ")) or ""
            drivers = re.findall(
                r"[A-Z][A-Za-z'.-]+\s+[A-Z][A-Za-z'.-]+",
                text
            )

        constructor = None
        if car_idx is not None and len(tds) > car_idx:
            constructor = clean(tds[car_idx].get_text())

        results.append({
            "finish_pos": pos,
            "drivers": drivers,
            "constructor": constructor
        })

    if not results:
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

    if year <= 2002:
        data = scrape_uniquecars(year)
    else:
        data = scrape_wikipedia(year)

    if not data:
        print("FAILED — keeping existing")
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

    print(f"saved {len(data['results'])} results")

    time.sleep(0.2)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("\nDONE")
