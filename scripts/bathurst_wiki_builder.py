import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST WIKI BUILDER (FIXED ROW PARSING)")

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


def clean(value):
    if value is None:
        return None
    value = str(value)
    value = re.sub(r"\[[^\]]*\]", "", value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value if value else None


def safe_int(value):
    if value is None:
        return None
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None


def fetch(url):
    try:
        response = SESSION.get(url, timeout=30)
        if response.status_code != 200:
            return None
        return response.text
    except Exception:
        return None


def split_early_drivers(text):
    text = clean(text)
    if not text:
        return []

    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace(" and ", "/")
    text = text.replace("&", "/")
    text = text.replace(",", "/")

    parts = [clean(x) for x in re.split(r"\s*/\s*", text) if clean(x)]
    if parts:
        return parts

    return [text]


def normalize_header(text):
    text = clean(text) or ""
    text = text.lower()
    text = text.replace("/", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_driver_names(cell):
    drivers = []

    # Preferred: linked names in the driver cell
    for a in cell.find_all("a"):
        name = clean(a.get_text(" ", strip=True))
        if not name:
            continue
        # Skip flag links / tiny labels; keep real names
        if " " not in name:
            continue
        if name.lower() in {"australia", "new zealand", "sweden", "france", "denmark", "brazil", "united kingdom"}:
            continue
        drivers.append(name)

    # Dedupe while preserving order
    deduped = []
    seen = set()
    for name in drivers:
        key = name.lower()
        if key not in seen:
            deduped.append(name)
            seen.add(key)

    if deduped:
        return deduped

    # Fallback: split visible text by line breaks
    raw = cell.get_text("\n", strip=True)
    raw = re.sub(r"\[[^\]]*\]", "", raw)
    pieces = [clean(x) for x in re.split(r"[\n/]+", raw) if clean(x)]

    fallback = []
    seen = set()
    for piece in pieces:
        if " " not in piece:
            continue
        key = piece.lower()
        if key not in seen:
            fallback.append(piece)
            seen.add(key)

    return fallback


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


def find_race_results_table(soup):
    # Find the "Race results" heading first
    race_heading = None
    for tag in soup.find_all(["h2", "h3"]):
        text = clean(tag.get_text(" ", strip=True)) or ""
        if "race results" in text.lower():
            race_heading = tag
            break

    search_root = race_heading if race_heading else soup

    # Look through tables after that heading and find the one with the exact columns
    for table in search_root.find_all_next("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        header_row = None
        headers = None

        for tr in rows[:3]:
            header_cells = tr.find_all("th", recursive=False)
            if len(header_cells) < 5:
                continue

            normalized = [normalize_header(th.get_text(" ", strip=True)) for th in header_cells]
            joined = " | ".join(normalized)

            if all(token in joined for token in ["pos", "no", "team", "drivers", "car"]):
                header_row = tr
                headers = normalized
                break

        if header_row is not None:
            return table, headers

    return None, None


def scrape_wikipedia(year):
    url = WIKI_BASE + quote(f"{year}_Bathurst_1000")
    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    table, headers = find_race_results_table(soup)

    if table is None:
        print(f"  no results table found for {year}")
        return None

    # Exact column indexes from the actual race results header
    pos_idx = next((i for i, h in enumerate(headers) if "pos" == h or h.startswith("pos ")), None)
    if pos_idx is None:
        pos_idx = next((i for i, h in enumerate(headers) if "pos" in h), None)

    no_idx = next((i for i, h in enumerate(headers) if h == "no" or h.startswith("no ")), None)
    team_idx = next((i for i, h in enumerate(headers) if "team" in h), None)
    drivers_idx = next((i for i, h in enumerate(headers) if "drivers" in h or h == "driver"), None)
    car_idx = next((i for i, h in enumerate(headers) if h == "car" or "car " in h or "car" in h), None)

    if pos_idx is None or drivers_idx is None or car_idx is None:
        print(f"  missing key columns for {year}")
        return None

    results = []
    rows = table.find_all("tr")

    started = False
    for tr in rows:
        direct_cells = tr.find_all(["th", "td"], recursive=False)
        if not direct_cells:
            continue

        # Skip until after the header row
        if not started:
            header_texts = [normalize_header(cell.get_text(" ", strip=True)) for cell in direct_cells]
            joined = " | ".join(header_texts)
            if all(token in joined for token in ["pos", "no", "team", "drivers", "car"]):
                started = True
            continue

        # IMPORTANT: use both th and td so column positions don't shift
        cells = tr.find_all(["th", "td"], recursive=False)
        if len(cells) <= max(pos_idx, drivers_idx, car_idx):
            continue

        pos = safe_int(cells[pos_idx].get_text(" ", strip=True))
        if pos is None:
            continue

        driver_cell = cells[drivers_idx]
        car_cell = cells[car_idx]

        drivers = extract_driver_names(driver_cell)
        constructor = clean(car_cell.get_text(" ", strip=True))

        # Skip junk rows that somehow are not real result rows
        if not drivers and not constructor:
            continue

        results.append({
            "finish_pos": pos,
            "drivers": drivers,
            "constructor": constructor
        })

    if not results:
        print(f"  no parsed rows for {year}")
        return None

    results.sort(key=lambda x: x["finish_pos"])

    return {
        "year": year,
        "results": results,
        "winner": results[0]["drivers"],
        "source": url
    }


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
