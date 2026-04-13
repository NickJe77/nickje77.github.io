import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (FINAL WORKING VERSION)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1963
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
    m = re.search(r"^\D*(\d+)", str(v))
    return int(m.group(1)) if m else None


def split_drivers(text):
    text = clean(text)
    if not text:
        return []

    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace(" and ", " / ")
    text = text.replace("&", "/")

    # normal split
    if "/" in text:
        parts = re.split(r"\s*/\s*", text)
        return [clean(p) for p in parts if clean(p)]

    # 🔥 FIX: split multiple full names in one string
    names = re.findall(r"[A-Z][A-Za-z'.-]+\s+[A-Z][A-Za-z'.-]+", text)
    if len(names) >= 2:
        return names

    return [text]


def fetch(url):
    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return None
        return r.text
    except:
        return None


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
                "drivers": split_drivers(cols[1]),
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
# WIKIPEDIA (2003+ FIXED)
# -----------------------
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


def scrape_wikipedia(year):
    slug = WIKI_PAGE_MAP.get(year, f"{year}_Bathurst_1000")
    url = WIKI_BASE + quote(slug)

    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    best_results = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        if len(rows) < 10:
            continue

        parsed = []
        for tr in rows:
            cols = tr.find_all(["td", "th"])
            row = [clean(c.get_text(" ", strip=True)) for c in cols]
            row = [x for x in row if x]
            if row:
                parsed.append(row)

        if len(parsed) < 10:
            continue

        header = " ".join(parsed[0]).lower()

        # STRICT FILTER
        if "driver" not in header:
            continue
        if "pos" not in header and "position" not in header:
            continue
        if "lap" not in header and "time" not in header:
            continue

        results = []

        for r in parsed[1:]:
            if len(r) < 3:
                continue

            pos = safe_int(r[0])
            if pos is None or pos > 100:
                continue

            drivers = split_drivers(r[2])

            if not drivers:
                continue

            d = " ".join(drivers).lower()
            if any(x in d for x in ["km", "pts", "team"]):
                continue

            constructor = None
            if len(r) > 4:
                constructor = r[4]

                if constructor and re.match(r"\d+[:.]\d+", constructor):
                    constructor = None

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

    if year <= 2002:
        data = scrape_uniquecars(year)
    else:
        data = scrape_wikipedia(year)

    if not data:
        print("  FAILED")
        continue

    out_file = SEASONS_DIR / f"{year}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    index.append({
        "year": year,
        "file": f"/data/bathurst/seasons/{year}.json"
    })

    print(f"  saved {len(data['results'])} results")

    time.sleep(0.3)

index.sort(key=lambda x: x["year"])

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("\nDONE")
