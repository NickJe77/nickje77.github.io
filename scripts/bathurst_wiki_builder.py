import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST WIKI BUILDER (2003+ ONLY, FIXED ROW PARSING)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2003  # do not touch 2002 and earlier
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0"
})

WIKI_PAGE_MAP = {
    2003: "2003_Bob_Jane_T-Marts_1000",
    2004: "2004_Bob_Jane_T-Marts_1000",
    2005: "2005_Supercheap_Auto_1000",
    2006: "2006_Supercheap_Auto_Bathurst_1000",
    2007: "2007_Supercheap_Auto_Bathurst_1000",
    2008: "2008_Supercheap_Auto_Bathurst_1000",
    2009: "2009_Supercheap_Auto_Bathurst_1000",
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


def clean(value):
    if value is None:
        return None
    value = str(value)
    value = re.sub(r"\[[^\]]*\]", "", value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value if value else None


def norm_header(value):
    value = clean(value) or ""
    value = value.lower()
    value = value.replace("/", " ")
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def safe_int(value):
    if value is None:
        return None
    m = re.search(r"\d+", str(value))
    return int(m.group()) if m else None


def fetch(url):
    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def slug_for_year(year):
    return WIKI_PAGE_MAP.get(year, f"{year}_Bathurst_1000")


def extract_driver_names(cell):
    # Pull linked names only from the drivers cell.
    names = []

    for a in cell.find_all("a"):
        text = clean(a.get_text(" ", strip=True))
        if not text or " " not in text:
            continue

        # Skip obvious non-driver links
        low = text.lower()
        if any(bad in low for bad in [
            "australia", "new zealand", "sweden", "denmark", "france",
            "united kingdom", "holden", "ford", "commodore", "falcon",
            "racing", "motorsport", "engineering", "team", "bathurst"
        ]):
            continue

        names.append(text)

    # De-dupe while keeping order
    out = []
    seen = set()
    for n in names:
        k = n.lower()
        if k not in seen:
            out.append(n)
            seen.add(k)

    if out:
        return out

    # Fallback: split visible text by line breaks/slashes
    raw = cell.get_text("\n", strip=True)
    raw = re.sub(r"\[[^\]]*\]", "", raw)
    parts = re.split(r"[\n/]+", raw)

    out = []
    seen = set()
    for part in parts:
        part = clean(part)
        if not part or " " not in part:
            continue
        k = part.lower()
        if k not in seen:
            out.append(part)
            seen.add(k)

    return out


def find_results_table(soup):
    """
    Find the actual race results table.
    We prefer a table whose header row contains:
    Pos, No, Team, Driver(s), Car/Vehicle
    """
    best = None

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        # look for the first row with enough header cells
        header_row = None
        for tr in rows[:3]:
            cells = tr.find_all(["th", "td"], recursive=False)
            headers = [norm_header(c.get_text(" ", strip=True)) for c in cells]
            text = " ".join(headers)
            if "pos" in text and "driver" in text and ("car" in text or "vehicle" in text):
                header_row = tr
                break

        if header_row is None:
            continue

        header_cells = header_row.find_all(["th", "td"], recursive=False)
        headers = [norm_header(c.get_text(" ", strip=True)) for c in header_cells]
        header_text = " ".join(headers)

        score = 0
        for key in ["pos", "no", "team", "driver"]:
            if key in header_text:
                score += 1
        if "car" in header_text or "vehicle" in header_text:
            score += 1
        if "laps" in header_text:
            score += 1
        if "time retired" in header_text or "time" in header_text:
            score += 1

        if best is None or score > best["score"]:
            best = {
                "table": table,
                "headers": headers,
                "score": score,
            }

    return best["table"], best["headers"] if best else (None, None)


def scrape_wikipedia(year):
    slug = slug_for_year(year)
    url = "https://en.wikipedia.org/wiki/" + quote(slug)

    html = fetch(url)
    if not html:
        print("  fetch failed")
        return None

    soup = BeautifulSoup(html, "html.parser")

    table, headers = find_results_table(soup)
    if table is None:
        print("  no results table found")
        return None

    try:
        pos_idx = next(i for i, h in enumerate(headers) if h == "pos" or h.startswith("pos "))
        no_idx = next(i for i, h in enumerate(headers) if h == "no" or h.startswith("no "))
        team_idx = next(i for i, h in enumerate(headers) if "team" in h)
        drivers_idx = next(i for i, h in enumerate(headers) if "driver" in h)
        car_idx = next(i for i, h in enumerate(headers) if "car" in h or "vehicle" in h)
    except StopIteration:
        print("  header mapping failed:", headers)
        return None

    results = []
    rows = table.find_all("tr")

    started = False
    for tr in rows:
        # IMPORTANT: read BOTH th and td so the Pos column doesn't disappear
        cells = tr.find_all(["th", "td"], recursive=False)
        if not cells:
            continue

        cell_text = [norm_header(c.get_text(" ", strip=True)) for c in cells]

        # skip until we hit the real header row
        if not started:
            row_text = " ".join(cell_text)
            if "pos" in row_text and "driver" in row_text and ("car" in row_text or "vehicle" in row_text):
                started = True
            continue

        # data rows must have enough cells for the mapped indexes
        if len(cells) <= max(pos_idx, no_idx, team_idx, drivers_idx, car_idx):
            continue

        pos = safe_int(cells[pos_idx].get_text(" ", strip=True))
        if pos is None:
            continue

        car_no = safe_int(cells[no_idx].get_text(" ", strip=True))
        team = clean(cells[team_idx].get_text(" ", strip=True))
        drivers = extract_driver_names(cells[drivers_idx])
        constructor = clean(cells[car_idx].get_text(" ", strip=True))

        results.append({
            "finish_pos": pos,
            "car_no": car_no,
            "team": team,
            "drivers": drivers,
            "constructor": constructor,
        })

    if not results:
        print("  no rows parsed")
        return None

    results.sort(key=lambda x: x["finish_pos"])

    return {
        "year": year,
        "results": results,
        "winner": results[0]["drivers"],
        "source": url,
    }


# -----------------------
# RUN (2003+ ONLY, SAFE)
# -----------------------
existing_index = []
if INDEX_FILE.exists():
    try:
        existing_index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        existing_index = []

index_map = {}
for item in existing_index:
    try:
        y = int(item.get("year"))
        index_map[y] = item
    except Exception:
        pass

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")
    file_path = SEASONS_DIR / f"{year}.json"

    data = scrape_wikipedia(year)

    # Do not overwrite if a scrape fails
    if not data:
        print("  skipped (kept existing)")
        if file_path.exists():
            index_map[year] = {
                "year": year,
                "file": f"/data/bathurst/seasons/{year}.json"
            }
        continue

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    index_map[year] = {
        "year": year,
        "file": f"/data/bathurst/seasons/{year}.json"
    }

    print(f"  saved {len(data['results'])} results")
    time.sleep(0.2)

# Preserve pre-2003 entries in index
for item in existing_index:
    try:
        y = int(item.get("year"))
        if y < 2003 and y not in index_map:
            index_map[y] = item
    except Exception:
        pass

final_index = [index_map[y] for y in sorted(index_map)]

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(final_index, f, indent=2, ensure_ascii=False)

print("\nDONE")
