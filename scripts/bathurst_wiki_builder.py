import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST WIKI BUILDER (2003+ ONLY)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 2003
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
        response = SESSION.get(url, timeout=30)
        if response.status_code != 200:
            return None
        return response.text
    except Exception:
        return None


def wiki_slug(year):
    return WIKI_PAGE_MAP.get(year, f"{year}_Bathurst_1000")


def looks_like_person(text):
    """
    Keep likely personal names, reject team/sponsor/car strings.
    """
    text = clean(text)
    if not text:
        return False

    low = text.lower()

    banned_bits = [
        "racing", "motorsport", "engineering", "performance", "team",
        "holden", "ford", "nissan", "commodore", "falcon", "mustang",
        "camaro", "mercedes", "bmw", "audi", "porsche", "toyota",
        "mobil", "castrol", "shell", "caltex", "repco", "red bull",
        "penrite", "monster", "supercheap", "hsv", "walkinshaw",
        "lap", "laps", "retired", "grid", "points"
    ]
    if any(bit in low for bit in banned_bits):
        return False

    words = text.split()
    if len(words) < 2 or len(words) > 4:
        return False

    # Allow names like "Greg Murphy", "Steven Richards", "Jan Magnussen"
    # but avoid all-caps acronyms and obvious junk.
    capitalized = 0
    for w in words:
        if re.match(r"^[A-Z][A-Za-z'`.-]+$", w):
            capitalized += 1

    return capitalized >= 2


def extract_drivers_from_cell(cell):
    """
    Pull only the first two real person-like lines from the Drivers cell.
    This avoids dragging in team, sponsor, car, or adjacent-row junk.
    """
    pieces = []

    # get text as separate lines from <br> / nested tags
    for s in cell.stripped_strings:
        t = clean(s)
        if t:
            pieces.append(t)

    # also split any joined text fragments just in case
    expanded = []
    for piece in pieces:
        for part in re.split(r"\n|/|,| & | and ", piece):
            part = clean(part)
            if part:
                expanded.append(part)

    drivers = []
    seen = set()

    for part in expanded:
        if not looks_like_person(part):
            continue
        key = part.lower()
        if key in seen:
            continue
        drivers.append(part)
        seen.add(key)
        if len(drivers) == 2:
            break

    return drivers


def find_results_table(soup):
    """
    Find the actual race results table by exact-style headers.
    We score tables and take the best match.
    """
    best_table = None
    best_headers = None
    best_score = -1

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        # look at first few rows for a header row
        for tr in rows[:3]:
            cells = tr.find_all(["th", "td"], recursive=False)
            if len(cells) < 5:
                continue

            headers = [norm_header(c.get_text(" ", strip=True)) for c in cells]
            joined = " ".join(headers)

            score = 0
            if "pos" in joined:
                score += 2
            if re.search(r"\bno\b", joined):
                score += 2
            if "team" in joined or "entrant" in joined:
                score += 2
            if "driver" in joined:
                score += 3
            if "car" in joined or "vehicle" in joined:
                score += 3
            if "laps" in joined:
                score += 1
            if "time retired" in joined or "time" in joined:
                score += 1

            # reject obvious non-results tables
            if "driver" not in joined or ("car" not in joined and "vehicle" not in joined):
                continue

            if score > best_score:
                best_score = score
                best_table = table
                best_headers = headers

    return best_table, best_headers


def scrape_wikipedia(year):
    url = "https://en.wikipedia.org/wiki/" + quote(wiki_slug(year))

    html = fetch(url)
    if not html:
        print("  fetch failed")
        return None

    soup = BeautifulSoup(html, "html.parser")

    table, headers = find_results_table(soup)
    if table is None or headers is None:
        print("  no results table found")
        return None

    try:
        pos_idx = next(i for i, h in enumerate(headers) if h == "pos" or h.startswith("pos "))
        drivers_idx = next(i for i, h in enumerate(headers) if "driver" in h)
        car_idx = next(i for i, h in enumerate(headers) if "car" in h or "vehicle" in h)
    except StopIteration:
        print("  header mapping failed:", headers)
        return None

    results = []
    rows = table.find_all("tr")

    started = False
    for tr in rows:
        # IMPORTANT: include th so the position column does not vanish
        cells = tr.find_all(["th", "td"], recursive=False)
        if not cells:
            continue

        row_headers = [norm_header(c.get_text(" ", strip=True)) for c in cells]
        row_joined = " ".join(row_headers)

        if not started:
            if "pos" in row_joined and "driver" in row_joined and ("car" in row_joined or "vehicle" in row_joined):
                started = True
            continue

        if len(cells) <= max(pos_idx, drivers_idx, car_idx):
            continue

        pos = safe_int(cells[pos_idx].get_text(" ", strip=True))
        if pos is None:
            continue

        driver_cell = cells[drivers_idx]
        car_cell = cells[car_idx]

        drivers = extract_drivers_from_cell(driver_cell)
        constructor = clean(car_cell.get_text(" ", strip=True))

        results.append({
            "finish_pos": pos,
            "drivers": drivers,
            "constructor": constructor
        })

    if not results:
        print("  no rows parsed")
        return None

    results.sort(key=lambda x: x["finish_pos"])

    return {
        "year": year,
        "results": results,
        "winner": results[0]["drivers"],
        "source": url
    }


def load_existing_index():
    if not INDEX_FILE.exists():
        return []
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def build_index(existing_index):
    index_map = {}

    # preserve anything already in the index, especially pre-2003
    for item in existing_index:
        try:
            y = int(item.get("year"))
            index_map[y] = item
        except Exception:
            continue

    for year in range(START_YEAR, END_YEAR + 1):
        path = SEASONS_DIR / f"{year}.json"
        if path.exists():
            index_map[year] = {
                "year": year,
                "file": f"/data/bathurst/seasons/{year}.json"
            }

    return [index_map[y] for y in sorted(index_map)]


# -----------------------
# RUN (2003+ ONLY)
# -----------------------
for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")
    file_path = SEASONS_DIR / f"{year}.json"

    data = scrape_wikipedia(year)

    # safe: do not overwrite on failure
    if not data:
        print("  skipped (kept existing)")
        continue

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  saved {len(data['results'])} results")
    time.sleep(0.2)

existing_index = load_existing_index()
final_index = build_index(existing_index)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(final_index, f, indent=2, ensure_ascii=False)

print("\nDONE")
