import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST CSV BUILDER (SAFE EARLY YEARS)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
CSV_FILE = BASE / "bathurst_export.csv"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1963
END_YEAR = datetime.utcnow().year

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

# ONLY NEEDED FOR 2003+
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

def clean(x):
    if not x:
        return ""
    x = str(x)
    x = re.sub(r"\[[^\]]*\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x

def safe_int(x):
    if not x:
        return ""
    m = re.search(r"\d+", str(x))
    return m.group() if m else ""

def fetch(url):
    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return None
        return r.text
    except:
        return None

def extract_drivers(cell):
    text = cell.get_text("\n", strip=True)
    parts = re.split(r"\n|/|,| & | and ", text)

    drivers = []
    for p in parts:
        p = clean(p)
        if not p:
            continue
        if len(p.split()) >= 2:
            drivers.append(p)

    return drivers[:2]

def scrape(year):
    slug = WIKI_PAGE_MAP.get(year)
    if not slug:
        return None

    url = "https://en.wikipedia.org/wiki/" + quote(slug)
    html = fetch(url)

    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "wikitable"})
    if not table:
        return None

    rows = table.find_all("tr")
    results = []

    for tr in rows[1:]:
        cells = tr.find_all(["td", "th"])
        if len(cells) < 5:
            continue

        pos = safe_int(cells[0].get_text())
        if not pos:
            continue

        drivers = extract_drivers(cells[2])
        constructor = clean(cells[3].get_text())

        results.append({
            "finish_pos": pos,
            "drivers": drivers,
            "constructor": constructor
        })

    return results


# -----------------------
# BUILD CSV ONLY (NO RISK)
# -----------------------

rows = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    file_path = SEASONS_DIR / f"{year}.json"

    # ✅ USE EXISTING DATA (EARLY YEARS SAFE)
    if file_path.exists():
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            results = data.get("results", [])
            print("using existing")
        except:
            results = []
    else:
        # ONLY SCRAPE 2003+
        if year >= 2003:
            print("scraping")
            results = scrape(year) or []
        else:
            results = []

    # ALWAYS OUTPUT ROW (NO GAPS)
    if not results:
        rows.append([year, "", "", "", ""])
        continue

    for r in results:
        d = r.get("drivers", [])
        d1 = d[0] if len(d) > 0 else ""
        d2 = d[1] if len(d) > 1 else ""

        rows.append([
            year,
            r.get("finish_pos", ""),
            d1,
            d2,
            r.get("constructor", "")
        ])

    time.sleep(0.2)

# WRITE CSV
with open(CSV_FILE, "w", encoding="utf-8") as f:
    f.write("year,position,driver_1,driver_2,constructor\n")
    for r in rows:
        f.write(",".join([str(x).replace(",", "") for x in r]) + "\n")

print(f"\nCSV COMPLETE → {CSV_FILE}")
