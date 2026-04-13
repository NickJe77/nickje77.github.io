import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST WIKIPEDIA BUILDER (FULL FIELD FIX)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1960
END_YEAR = min(datetime.utcnow().year, 2026)

HEADERS = {"User-Agent": "Mozilla/5.0"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

WIKI = "https://en.wikipedia.org/wiki/"


# -----------------------
# BASIC HELPERS
# -----------------------
def clean_text(v):
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
    v = clean_text(v)
    if not v:
        return None
    m = re.search(r"\d+", v)
    return int(m.group()) if m else None


def split_drivers(text):
    text = clean_text(text)
    if not text:
        return []

    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace(" and ", " / ").replace("&", "/")

    if "/" in text:
        parts = re.split(r"\s*/\s*", text)
        return [clean_text(p) for p in parts if clean_text(p)]

    # handle "Barry Ferguson Bill Ford"
    tokens = text.split()
    if len(tokens) == 4:
        return [f"{tokens[0]} {tokens[1]}", f"{tokens[2]} {tokens[3]}"]

    names = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", text)
    if len(names) >= 2:
        return names

    return [text]


# -----------------------
# PAGE MAP
# -----------------------
PAGE_MAP = {
    1960: "1960_Armstrong_500",
    1961: "1961_Armstrong_500",
    1962: "1962_Armstrong_500",
    1963: "1963_Armstrong_500",
    1964: "1964_Armstrong_500",
    1965: "1965_Armstrong_500",
    1966: "1966_Armstrong_500",
    1967: "1967_Gallaher_500",
    1968: "1968_Hardie-Ferodo_500",
    1969: "1969_Hardie-Ferodo_500",
    1970: "1970_Hardie-Ferodo_500",
    1971: "1971_Hardie-Ferodo_500",
    1972: "1972_Hardie-Ferodo_500",
    1973: "1973_Hardie-Ferodo_1000",
    1974: "1974_Hardie-Ferodo_1000",
    1975: "1975_Hardie-Ferodo_1000",
    1976: "1976_Hardie-Ferodo_1000",
    1977: "1977_Hardie-Ferodo_1000",
    1978: "1978_Hardie-Ferodo_1000",
    1979: "1979_Hardie-Ferodo_1000",
    1980: "1980_Hardie-Ferodo_1000",
    1981: "1981_James_Hardie_1000",
    1982: "1982_James_Hardie_1000",
    1983: "1983_James_Hardie_1000",
    1984: "1984_James_Hardie_1000",
    1985: "1985_James_Hardie_1000",
    1986: "1986_James_Hardie_1000",
    1987: "1987_James_Hardie_1000",
    1988: "1988_Tooheys_1000",
    1989: "1989_Tooheys_1000",
    1990: "1990_Tooheys_1000",
    1991: "1991_Tooheys_1000",
    1992: "1992_Tooheys_1000",
    1993: "1993_Tooheys_1000",
    1994: "1994_Tooheys_1000",
    1995: "1995_Tooheys_1000",
    1996: "1996_AMP_Bathurst_1000",
    1997: "1997_Primus_1000_Classic",
    1998: "1998_FAI_1000",
    1999: "1999_FAI_1000",
    2000: "2000_FAI_1000",
    2001: "2001_Australian_1000_Classic",
    2002: "2002_Bob_Jane_T-Marts_1000",
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


def fetch_page(year):
    slug = PAGE_MAP.get(year)
    if not slug:
        return None, None

    url = WIKI + quote(slug)
    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return url, None
        return url, r.text
    except:
        return url, None


# -----------------------
# TABLE PARSER
# -----------------------
def parse_page(year, url, html):
    soup = BeautifulSoup(html, "html.parser")

    results = []

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 10:
            continue

        parsed = []
        for tr in rows:
            cols = tr.find_all(["td", "th"])
            if len(cols) < 3:
                continue

            row = [clean_text(c.get_text(" ", strip=True)) for c in cols]
            if row:
                parsed.append(row)

        if len(parsed) < 10:
            continue

        for r in parsed[1:]:
            pos = safe_int(r[0])
            if pos is None:
                continue

            drivers = split_drivers(" ".join(r))

            results.append({
                "finish_pos": pos,
                "car_no": r[1] if len(r) > 1 else None,
                "drivers": drivers,
                "team": None,
                "car": None,
                "laps": None,
                "time": None,
                "gap": None,
                "status": None
            })

        if len(results) > 20:
            break

    winner = []
    for r in results:
        if r["finish_pos"] == 1:
            winner = r["drivers"]
            break

    return {
        "year": year,
        "title": str(year),
        "name": str(year),
        "date": None,
        "venue": None,
        "url": url,
        "winner": winner,
        "grid": [],
        "results": results,
        "grid_count": 0,
        "result_count": len(results)
    }


# -----------------------
# RUN
# -----------------------
index = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    url, html = fetch_page(year)

    if not html:
        print("  failed")
        continue

    data = parse_page(year, url, html)

    with open(SEASONS_DIR / f"{year}.json", "w") as f:
        json.dump(data, f, indent=2)

    index.append({
        "year": year,
        "file": f"/data/bathurst/seasons/{year}.json"
    })

    print(f"  saved {data['result_count']} results")

    time.sleep(0.3)

with open(INDEX_FILE, "w") as f:
    json.dump(index, f, indent=2)

print("\nDONE")
