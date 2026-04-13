import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (FINAL CLEAN VERSION)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1963
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})


# -----------------------
# HELPERS
# -----------------------
def clean(v):
    if not v:
        return None
    v = re.sub(r"\[[^\]]*\]", "", str(v))
    v = v.replace("\xa0", " ")
    v = re.sub(r"\s+", " ", v).strip()
    return v if v else None


def safe_int(v):
    if not v:
        return None
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else None


def split_drivers(text):
    text = clean(text)
    if not text:
        return []
    parts = re.split(r"/|&| and ", text)
    return [clean(p) for p in parts if clean(p)]


# -----------------------
# UNIQUECARS (1963–2002)
# -----------------------
def scrape_uniquecars(year):
    url = f"https://www.uniquecarsandparts.com/bathurst_{year}.htm"

    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return None
    except:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    for tr in soup.find_all("tr"):
        cols = [clean(td.get_text()) for td in tr.find_all("td")]

        if len(cols) < 4:
            continue

        pos = safe_int(cols[0])
        if pos is None:
            continue

        results.append({
            "finish_pos": pos,
            "drivers": split_drivers(cols[1]),
            "constructor": cols[2]
        })

    if not results:
        return None

    return results


# -----------------------
# WIKIPEDIA (2003+)
# -----------------------
def scrape_wiki(year):
    url = f"https://en.wikipedia.org/wiki/{year}_Bathurst_1000"

    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return None
    except:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        if len(rows) < 10:
            continue

        for tr in rows[1:]:
            cols = [clean(td.get_text()) for td in tr.find_all("td")]

            if len(cols) < 3:
                continue

            pos = safe_int(cols[0])
            if pos is None:
                continue

            results.append({
                "finish_pos": pos,
                "drivers": split_drivers(cols[2]),
                "constructor": cols[4] if len(cols) > 4 else None
            })

        if len(results) > 20:
            break

    if not results:
        return None

    return results


# -----------------------
# RUN
# -----------------------
index = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    if year <= 2002:
        results = scrape_uniquecars(year)
    else:
        results = scrape_wiki(year)

    if not results:
        print("  FAILED")
        continue

    data = {
        "year": year,
        "results": results,
        "winner": results[0]["drivers"] if results else []
    }

    with open(SEASONS_DIR / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    index.append({
        "year": year,
        "file": f"/data/bathurst/seasons/{year}.json"
    })

    print(f"  saved {len(results)} results")

    time.sleep(0.3)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("\nDONE")
