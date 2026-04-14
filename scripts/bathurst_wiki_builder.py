import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (FINAL - DYNAMIC COLUMN FIX)")

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
# FIND COLUMN INDEX BY HEADER
# -----------------------
def find_column_indexes(header_row):
    headers = [h.get_text(" ").lower() for h in header_row.find_all(["th", "td"])]

    col_map = {}

    for i, h in enumerate(headers):
        if "pos" in h:
            col_map["pos"] = i
        elif "driver" in h:
            col_map["drivers"] = i
        elif "car" in h or "vehicle" in h:
            col_map["car"] = i

    return col_map


# -----------------------
# UNIQUECARS (SAFE)
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
                "drivers": [cols[1]],
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
# WIKIPEDIA (DYNAMIC)
# -----------------------
def scrape_wikipedia(year):
    url = WIKI_BASE + quote(f"{year}_Bathurst_1000")

    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    best_results = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 5:
            continue

        col_map = find_column_indexes(rows[0])

        if "pos" not in col_map or "drivers" not in col_map:
            continue

        results = []

        for tr in rows[1:]:
            cells = tr.find_all("td")
            if len(cells) <= max(col_map.values()):
                continue

            pos = safe_int(cells[col_map["pos"]].get_text())
            if pos is None:
                continue

            driver_cell = cells[col_map["drivers"]]

            drivers = []

            # ✅ GET ALL <a> TAGS
            for a in driver_cell.find_all("a"):
                name = clean(a.get_text())
                if name and " " in name:
                    drivers.append(name)

            # fallback if needed
            if not drivers:
                text = clean(driver_cell.get_text(" ")) or ""
                drivers = re.findall(
                    r"[A-Z][A-Za-z'.-]+\s+[A-Z][A-Za-z'.-]+",
                    text
                )

            constructor = None
            if "car" in col_map and len(cells) > col_map["car"]:
                constructor = clean(cells[col_map["car"]].get_text())

            results.append({
                "finish_pos": pos,
                "drivers": drivers,
                "constructor": constructor
            })

        if len(results) > len(best_results):
            best_results = results

    if not best_results:
        return None

    best_results.sort(key=lambda x: x["finish_pos"])

    return {
        "year": year,
        "results": best_results,
        "winner": best_results[0]["drivers"],
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

    time.sleep(0.3)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("\nDONE")
