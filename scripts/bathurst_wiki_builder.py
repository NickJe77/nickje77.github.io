import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST SAFE FIXER")

BASE = Path("docs/data/bathurst/seasons")

START_YEAR = 2003
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})


def clean(v):
    if not v:
        return None
    v = str(v)
    v = re.sub(r"\[[^\]]*\]", "", v)
    return re.sub(r"\s+", " ", v).strip()


def safe_int(v):
    if not v:
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
# CHECK IF FILE IS BROKEN
# -----------------------
def is_broken(path):
    try:
        data = json.loads(path.read_text())
        for r in data.get("results", []):
            if not r.get("drivers") or len(r.get("drivers")) < 2:
                return True
        return False
    except:
        return True


# -----------------------
# SCRAPER (ROWSPAN SAFE)
# -----------------------
def scrape_year(year):
    url = "https://en.wikipedia.org/wiki/" + quote(f"{year}_Bathurst_1000")
    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    table = None
    for t in soup.find_all("table"):
        if "driver" in t.get_text(" ").lower() and "pos" in t.get_text(" ").lower():
            table = t
            break

    if not table:
        return None

    results = []
    current = None

    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue

        pos = safe_int(cells[0].get_text())

        if pos:
            if current:
                results.append(current)

            current = {
                "finish_pos": pos,
                "drivers": [],
                "constructor": None
            }

            if len(cells) > 3:
                name = clean(cells[3].get_text())
                if name and len(name.split()) >= 2:
                    current["drivers"].append(name)

            if len(cells) > 4:
                current["constructor"] = clean(cells[4].get_text())

        else:
            if current and len(cells) > 3:
                name = clean(cells[3].get_text())
                if name and len(name.split()) >= 2:
                    current["drivers"].append(name)

    if current:
        results.append(current)

    return {
        "year": year,
        "results": results,
        "winner": results[0]["drivers"] if results else [],
        "source": url
    }


# -----------------------
# RUN (SAFE MODE)
# -----------------------
for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    path = BASE / f"{year}.json"

    if path.exists() and not is_broken(path):
        print("SKIPPED (already good)")
        continue

    print("FIXING...")

    data = scrape_year(year)

    if not data:
        print("FAILED")
        continue

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    print("UPDATED")

    time.sleep(0.2)

print("\nDONE")
