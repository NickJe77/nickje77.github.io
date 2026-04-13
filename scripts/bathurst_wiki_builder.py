import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (RESULTS ONLY: FINISH / DRIVERS / CONSTRUCTOR)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1963
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

WIKI_BASE = "https://en.wikipedia.org/wiki/"


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def clean(v):
    if v is None:
        return None
    v = str(v)
    v = re.sub(r"\[[^\]]*\]", "", v)
    v = v.replace("\xa0", " ")
    v = v.replace("†", "")
    v = v.replace("‡", "")
    v = re.sub(r"\s+", " ", v).strip()
    return v if v else None


def safe_int(v):
    if v is None:
        return None
    m = re.search(r"^\D*(\d+)\D*$", str(v).strip())
    return int(m.group(1)) if m else None


def split_drivers(text):
    text = clean(text)
    if not text:
        return []

    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace(" and ", " / ")
    text = text.replace("&", "/")
    text = text.replace(" + ", " / ")
    text = re.sub(r"\s*/\s*", " / ", text)

    if " / " in text:
        parts = [clean(x) for x in text.split(" / ") if clean(x)]
        return dedupe(parts)

    # very common old format: "Barry Ferguson Bill Ford"
    tokens = text.split()
    if len(tokens) == 4:
        return [f"{tokens[0]} {tokens[1]}", f"{tokens[2]} {tokens[3]}"]

    # find multiple full names
    names = re.findall(r"[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+)+", text)
    if len(names) >= 2:
        return dedupe([clean(x) for x in names if clean(x)])

    return [text]


def dedupe(items):
    out = []
    seen = set()
    for item in items:
        item = clean(item)
        if not item:
            continue
        k = item.lower()
        if k not in seen:
            out.append(item)
            seen.add(k)
    return out


def is_name_like(text):
    text = clean(text)
    if not text:
        return False

    low = text.lower()

    # obvious non-driver text
    banned = [
        "racing team", "racing", "engineering", "motorsport", "motorsports",
        "holden", "ford", "mustang", "camaro", "commodore", "nissan", "bmw",
        "audi", "chevrolet", "pts", "point", "km", "lap", "laps", "time",
        "top 10", "shootout", "grid", "qualifying", "pole"
    ]
    if any(x in low for x in banned):
        return False

    # looks like one or more person names
    return bool(re.search(r"[A-Z][A-Za-z'.-]+\s+[A-Z][A-Za-z'.-]+", text))


def find_heading_text(table):
    heading = ""
    node = table
    while True:
        node = node.find_previous(["h2", "h3", "h4"])
        if not node:
            break
        heading = clean(node.get_text(" ", strip=True)) or ""
        heading = heading.replace("[edit]", "").strip()
        if heading:
            break
    return heading.lower()


def fetch(url):
    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


# --------------------------------------------------
# UNIQUE CARS: 1963-2002
# --------------------------------------------------
def parse_uniquecars_table(table):
    rows = []
    trs = table.find_all("tr")
    if len(trs) < 8:
        return []

    for tr in trs:
        cols = [clean(td.get_text(" ", strip=True)) for td in tr.find_all("td")]
        cols = [x for x in cols if x is not None]

        if len(cols) < 3:
            continue

        pos = safe_int(cols[0])
        if pos is None:
            continue

        drivers = split_drivers(cols[1])

        # constructor is usually col 2 on UniqueCars
        constructor = cols[2] if len(cols) > 2 else None

        if not drivers:
            continue

        rows.append({
            "finish_pos": pos,
            "drivers": drivers,
            "constructor": constructor
        })

    rows.sort(key=lambda x: x["finish_pos"])
    return rows


def scrape_uniquecars(year):
    url = f"https://www.uniquecarsandparts.com/bathurst_{year}.htm"
    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    best = []
    for table in soup.find_all("table"):
        candidate = parse_uniquecars_table(table)
        if len(candidate) > len(best):
            best = candidate

    if not best:
        return None

    return {
        "year": year,
        "results": best,
        "winner": best[0]["drivers"] if best else [],
        "source": url
    }


# --------------------------------------------------
# WIKIPEDIA: 2003+
# --------------------------------------------------
WIKI_PAGE_MAP = {
    2003: "2003_Bob_Jane_T-Marts_1000",
    2004: "2004_Bob_Jane_T-Marts_1000",
    2005: "2005_SUPERCHEAP_AUTO_Bathurst_1000",
    2006: "2006_SUPERCHEAP_AUTO_Bathurst_1000",
    2007: "2007_SUPERCHEAP_AUTO_Bathurst_1000",
    2008: "2008_SUPERCHEAP_AUTO_Bathurst_1000",
    2009: "2009_SUPERCHEAP_AUTO_Bathurst_1000",
    2010: "2010_Supercheap_Auto_Bathurst_1000",
    2011: "2011_Supercheap_Auto_Bathurst_1000",
    2012: "2012_Supercheap_Auto_Bathurst_1000",
    2013: "2013_Supercheap_Auto_Bathurst_1000",
    2014: "2014_Supercheap_Auto_Bathurst_1000",
    2015: "2015_Supercheap_Auto_Bathurst_1000",
    2016: "2016_Supercheap_Auto_Bathurst_1000",
    2017: "2017_Supercheap_Auto_Bathurst_1000",
    2018: "2018_Supercheap_Auto_Bathurst_1000",
    2019: "2019_Supercheap_Auto_Bathurst_1000",
    2020: "2020_Supercheap_Auto_Bathurst_1000",
    2021: "2021_Bathurst_1000",
    2022: "2022_Bathurst_1000",
    2023: "2023_Bathurst_1000",
    2024: "2024_Bathurst_1000",
    2025: "2025_Bathurst_1000",
    2026: "2026_Bathurst_1000",
}


def table_headers(table):
    headers = []
    first_rows = table.find_all("tr")[:3]
    for tr in first_rows:
        hs = [clean(x.get_text(" ", strip=True)) for x in tr.find_all(["th", "td"])]
        hs = [x for x in hs if x]
        if hs:
            headers.append(hs)
    return headers


def choose_results_table(soup):
    candidates = []

    for table in soup.find_all("table"):
        trs = table.find_all("tr")
        if len(trs) < 8:
            continue

        heading = find_heading_text(table)
        headers_nested = table_headers(table)
        flat_headers = " | ".join(" | ".join(x).lower() for x in headers_nested)

        # reject obvious junk
        reject_words = [
            "top 10", "shootout", "qualifying", "practice", "championship",
            "standings", "points", "support race", "support races", "drivers' championship",
            "manufacturers", "teams championship", "practice sessions"
        ]
        if any(x in heading for x in reject_words) or any(x in flat_headers for x in reject_words):
            continue

        score = 0

        # prefer real race/results sections
        if any(x in heading for x in ["race", "results", "classification", "classified"]):
            score += 5

        # prefer tables with real race-result columns
        if any(x in flat_headers for x in ["pos", "position"]):
            score += 2
        if "driver" in flat_headers or "drivers" in flat_headers:
            score += 3
        if any(x in flat_headers for x in ["car", "model", "vehicle", "constructor"]):
            score += 2
        if any(x in flat_headers for x in ["laps", "time", "gap", "status"]):
            score += 2

        # penalise obvious non-result tables
        if "grid" in flat_headers or "grid" in heading:
            score -= 3
        if "pole" in flat_headers or "pole" in heading:
            score -= 3

        if score > 0:
            candidates.append((score, len(trs), table, heading, flat_headers))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


def header_index(header_row):
    idx = {}
    for i, h in enumerate(header_row):
        h_low = (h or "").lower()
        idx[h_low] = i
    return idx


def find_col(headers, needles):
    for i, h in enumerate(headers):
        low = (h or "").lower()
        for needle in needles:
            if needle in low:
                return i
    return None


def parse_wiki_results_table(table):
    trs = table.find_all("tr")
    parsed_rows = []

    for tr in trs:
        cells = tr.find_all(["th", "td"])
        row = [clean(c.get_text(" ", strip=True)) for c in cells]
        row = [x for x in row if x is not None]
        if row:
            parsed_rows.append(row)

    if len(parsed_rows) < 3:
        return []

    # choose the most likely header row
    header_row = None
    data_start = 1

    for i, row in enumerate(parsed_rows[:3]):
        row_text = " | ".join(row).lower()
        if any(x in row_text for x in ["pos", "position"]) and ("driver" in row_text or "drivers" in row_text):
            header_row = row
            data_start = i + 1
            break

    if header_row is None:
        header_row = parsed_rows[0]
        data_start = 1

    pos_col = find_col(header_row, ["position", "pos"])
    driver_col = find_col(header_row, ["drivers", "driver"])
    car_col = find_col(header_row, ["car", "model", "vehicle", "constructor"])

    # some tables use Team then Car, some use only Car; driver col is essential
    if pos_col is None or driver_col is None:
        return []

    results = []

    for row in parsed_rows[data_start:]:
        if len(row) <= max(pos_col, driver_col):
            continue

        pos = safe_int(row[pos_col])
        if pos is None:
            continue

        drivers_text = row[driver_col]
        drivers = split_drivers(drivers_text)

        if not drivers:
            continue

        constructor = row[car_col] if car_col is not None and len(row) > car_col else None

        # reject junk rows that still slipped through
        if constructor and re.search(r"^\d+[:.]\d+", constructor):
            continue
        if len(drivers) == 1 and not is_name_like(drivers[0]):
            continue

        results.append({
            "finish_pos": pos,
            "drivers": drivers,
            "constructor": constructor
        })

    # dedupe exact rows
    deduped = []
    seen = set()
    for r in results:
        key = (r["finish_pos"], "|".join(r["drivers"]).lower(), (r["constructor"] or "").lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    deduped.sort(key=lambda x: x["finish_pos"])
    return deduped


def scrape_wikipedia(year):
    slug = WIKI_PAGE_MAP.get(year, f"{year}_Bathurst_1000")
    url = WIKI_BASE + quote(slug)
    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    table = choose_results_table(soup)
    if table is None:
        return None

    results = parse_wiki_results_table(table)
    if not results:
        return None

    return {
        "year": year,
        "results": results,
        "winner": results[0]["drivers"] if results else [],
        "source": url
    }


# --------------------------------------------------
# RUN
# --------------------------------------------------
index = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    if year <= 2002:
        data = scrape_uniquecars(year)
    else:
        data = scrape_wikipedia(year)

    if not data:
        print("  FAILED")
        continue

    out_file = SEASONS_DIR / f"{year}.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    index.append({
        "year": year,
        "file": f"/data/bathurst/seasons/{year}.json"
    })

    print(f"  saved {len(data['results'])} results")

    time.sleep(0.3)

index.sort(key=lambda x: x["year"])

with INDEX_FILE.open("w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("\nDONE")
