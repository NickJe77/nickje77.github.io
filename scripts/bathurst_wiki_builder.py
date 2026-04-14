import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (FIXED RESULTS COLUMNS)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1963
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0"
})

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
    except Exception:
        return None


def split_early_drivers(text):
    text = clean(text)
    if not text:
        return []

    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace(" and ", "/")
    text = text.replace("&", "/")

    parts = [clean(x) for x in re.split(r"\s*/\s*", text) if clean(x)]
    if parts:
        return parts

    return [text]


def normalize_header_text(text):
    text = clean(text) or ""
    text = text.lower()
    text = text.replace("/", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_driver_names_from_cell(cell):
    names = []

    # First try linked names in the cell
    for a in cell.find_all("a"):
        name = clean(a.get_text(" ", strip=True))
        if not name:
            continue
        # Real driver names are multi-word; ignore empty / flag links
        if " " in name:
            names.append(name)

    # De-duplicate while preserving order
    deduped = []
    seen = set()
    for name in names:
        key = name.lower()
        if key not in seen:
            deduped.append(name)
            seen.add(key)

    if deduped:
        return deduped

    # Fallback: text split by line breaks or separators
    raw = cell.get_text("\n", strip=True)
    raw = re.sub(r"\[[^\]]*\]", "", raw)
    bits = re.split(r"[\n/]+", raw)

    fallback = []
    seen = set()
    for bit in bits:
        bit = clean(bit)
        if not bit or " " not in bit:
            continue
        key = bit.lower()
        if key not in seen:
            fallback.append(bit)
            seen.add(key)

    return fallback


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
            cols = [clean(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
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
# WIKIPEDIA (2003+)
# -----------------------
def find_results_table(soup):
    """
    Find the actual race results table by looking for the expected
    Bathurst results headers:
    Pos | No | Team | Drivers | Car | ...
    """
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        header_row = None
        for tr in rows[:3]:
            ths = tr.find_all("th")
            if len(ths) >= 5:
                header_row = tr
                break

        if header_row is None:
            continue

        headers = [normalize_header_text(th.get_text(" ", strip=True)) for th in header_row.find_all("th")]

        needed = {"pos", "no", "team", "drivers", "car"}
        if needed.issubset(set(headers)):
            return table, headers

    return None, None


def scrape_wikipedia(year):
    url = WIKI_BASE + quote(f"{year}_Bathurst_1000")
    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    table, headers = find_results_table(soup)
    if table is None:
        return None

    # Exact header positions from the actual table we found
    col_idx = {h: i for i, h in enumerate(headers)}

    pos_idx = col_idx["pos"]
    drivers_idx = col_idx["drivers"]
    car_idx = col_idx["car"]

    results = []
    rows = table.find_all("tr")

    started = False
    for tr in rows:
        ths = tr.find_all("th")
        if ths and not started:
            row_headers = [normalize_header_text(th.get_text(" ", strip=True)) for th in ths]
            if set(["pos", "no", "team", "drivers", "car"]).issubset(set(row_headers)):
                started = True
            continue

        if not started:
            continue

        tds = tr.find_all("td", recursive=False)
        if not tds:
            tds = tr.find_all("td")

        if len(tds) <= max(pos_idx, drivers_idx, car_idx):
            continue

        pos = safe_int(tds[pos_idx].get_text(" ", strip=True))
        if pos is None:
            continue

        driver_cell = tds[drivers_idx]
        car_cell = tds[car_idx]

        drivers = extract_driver_names_from_cell(driver_cell)
        constructor = clean(car_cell.get_text(" ", strip=True))

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
# RUN (SAFE)
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
        print("  FAILED — keeping existing file")
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
