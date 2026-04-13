import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup

print("BATHURST WIKIPEDIA BUILDER (FORCE SAVE VERSION)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1960
END_YEAR = min(datetime.utcnow().year, 2026)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

WIKI = "https://en.wikipedia.org/wiki/"


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
    text = text.replace(" and ", " / ")
    text = text.replace(" & ", " / ")
    text = re.sub(r"\s*/\s*", " / ", text)

    parts = [clean_text(x) for x in text.split(" / ") if clean_text(x)]

    out = []
    seen = set()
    for p in parts:
        low = p.lower()
        if low not in seen:
            out.append(p)
            seen.add(low)
    return out


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
    except Exception:
        return url, None


def get_heading(table_tag):
    for tag in table_tag.find_all_previous(["h2", "h3", "h4"]):
        txt = clean_text(tag.get_text(" ", strip=True))
        if txt:
            return txt.lower().replace("[edit]", "").strip()
    return ""


def normalize_columns(df):
    cols = []
    for i, c in enumerate(df.columns):
        if isinstance(c, tuple):
            c = " ".join(str(x) for x in c if str(x) != "nan")
        c = clean_text(c) or f"col_{i+1}"
        cols.append(c)
    df = df.copy()
    df.columns = cols
    return df


def score_table(df, heading):
    cols = " | ".join(str(c).lower() for c in df.columns)
    heading = (heading or "").lower()

    grid_score = 0
    result_score = 0

    if any(x in heading for x in ["grid", "starting grid", "qualifying", "shootout"]):
        grid_score += 8
    if any(x in heading for x in ["race", "results", "classification"]):
        result_score += 8

    if any(x in cols for x in ["driver", "co-driver", "team", "car", "number", "no.", "pos", "position"]):
        grid_score += 2
        result_score += 2

    if any(x in cols for x in ["laps", "gap", "status", "time"]):
        result_score += 3

    if any(x in cols for x in ["qualifying", "grid"]):
        grid_score += 3

    return grid_score, result_score


def pick_val(record, needles):
    low = {str(k).lower(): v for k, v in record.items()}
    for needle in needles:
        for k, v in low.items():
            if needle in k:
                return clean_text(v)
    return None


def extract_drivers(record):
    drivers = []

    d1 = pick_val(record, ["co-driver", "co driver", "codriver"])
    d2 = pick_val(record, ["driver"])

    if d2:
        drivers.extend(split_drivers(d2))
    if d1:
        drivers.extend(split_drivers(d1))

    if not drivers:
        for k, v in record.items():
            txt = clean_text(v)
            if not txt:
                continue
            if "/" in txt and re.search(r"[A-Z][a-z]", txt):
                drivers = split_drivers(txt)
                if drivers:
                    break

    out = []
    seen = set()
    for d in drivers:
        k = d.lower()
        if k not in seen:
            out.append(d)
            seen.add(k)
    return out


def normalize_grid(df):
    rows = []
    for record in df.fillna("").to_dict(orient="records"):
        pos = safe_int(pick_val(record, ["grid", "position", "pos"]))
        if pos is None:
            continue

        rows.append({
            "grid_pos": pos,
            "car_no": pick_val(record, ["car no", "number", "no.", "no", "#"]),
            "drivers": extract_drivers(record),
            "team": pick_val(record, ["team", "entrant"]),
            "car": pick_val(record, ["car", "model", "vehicle"]),
            "qualifying_time": pick_val(record, ["qualifying time", "time"]),
        })

    seen = set()
    out = []
    for row in rows:
        ident = (
            row["grid_pos"],
            row["car_no"],
            "|".join(row["drivers"]),
            row["car"],
        )
        if ident in seen:
            continue
        seen.add(ident)
        out.append(row)

    out.sort(key=lambda x: x["grid_pos"])
    return out


def normalize_results(df):
    rows = []
    for record in df.fillna("").to_dict(orient="records"):
        pos_raw = pick_val(record, ["position", "pos", "place"])
        pos = safe_int(pos_raw)

        drivers = extract_drivers(record)
        car = pick_val(record, ["car", "model", "vehicle"])

        if pos is None and not drivers and not car:
            continue

        rows.append({
            "finish_pos": pos if pos is not None else pos_raw,
            "car_no": pick_val(record, ["car no", "number", "no.", "no", "#"]),
            "drivers": drivers,
            "team": pick_val(record, ["team", "entrant"]),
            "car": car,
            "laps": pick_val(record, ["laps", "lap"]),
            "time": pick_val(record, ["total time", "race time", "time"]),
            "gap": pick_val(record, ["gap"]),
            "status": pick_val(record, ["status", "reason"]),
        })

    def sort_key(x):
        v = x["finish_pos"]
        if isinstance(v, int):
            return (0, v)
        m = re.search(r"\d+", str(v or ""))
        if m:
            return (0, int(m.group()))
        return (1, 9999)

    seen = set()
    out = []
    for row in rows:
        ident = (
            str(row["finish_pos"]),
            row["car_no"],
            "|".join(row["drivers"]),
            row["car"],
        )
        if ident in seen:
            continue
        seen.add(ident)
        out.append(row)

    out.sort(key=sort_key)
    return out


def parse_infobox(soup, year, url):
    title = clean_text(soup.find("h1").get_text(" ", strip=True)) if soup.find("h1") else str(year)

    date = None
    venue = None

    infobox = soup.find("table", class_=lambda c: c and "infobox" in c)
    if infobox:
        for tr in infobox.find_all("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue
            key = clean_text(th.get_text(" ", strip=True))
            val = clean_text(td.get_text(" ", strip=True))
            if not key or not val:
                continue

            low = key.lower()
            if low == "date" and not date:
                m = re.search(r"\b(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", val)
                date = m.group(1) if m else val
            if any(x in low for x in ["location", "venue", "circuit"]) and not venue:
                venue = val

    return {
        "year": year,
        "title": title,
        "name": title,
        "date": date,
        "venue": venue,
        "url": url,
    }


def parse_page(year, url, html):
    soup = BeautifulSoup(html, "html.parser")
    meta = parse_infobox(soup, year, url)

    grid = []
    results = []

    candidate_grids = []
    candidate_results = []

    for table_tag in soup.find_all("table", class_=lambda c: c and "wikitable" in c):
        heading = get_heading(table_tag)

        try:
            dfs = pd.read_html(str(table_tag))
        except Exception:
            dfs = []

        for df in dfs:
            try:
                df = normalize_columns(df)
                gscore, rscore = score_table(df, heading)

                if gscore >= 5:
                    ng = normalize_grid(df)
                    if ng:
                        candidate_grids.append((len(ng), gscore, ng, heading, list(df.columns)))

                if rscore >= 5:
                    nr = normalize_results(df)
                    if nr:
                        candidate_results.append((len(nr), rscore, nr, heading, list(df.columns)))
            except Exception:
                pass

    if candidate_grids:
        candidate_grids.sort(key=lambda x: (x[1], x[0]), reverse=True)
        grid = candidate_grids[0][2]

    if candidate_results:
        candidate_results.sort(key=lambda x: (x[0], x[1]), reverse=True)
        results = candidate_results[0][2]

    winner = results[0]["drivers"] if results and results[0]["drivers"] else []

    meta["winner"] = winner
    meta["grid_count"] = len(grid)
    meta["result_count"] = len(results)
    meta["grid"] = grid
    meta["results"] = results

    return meta


index = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    url, html = fetch_page(year)

    if not html:
        print("  page failed")
        continue

    try:
        data = parse_page(year, url, html)

        # force save if we found anything at all
        if not data["grid"] and not data["results"]:
            print("  no parsed tables, saving stub anyway")

        out_file = SEASONS_DIR / f"{year}.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        index.append({
            "year": year,
            "title": data["title"],
            "name": data["name"],
            "date": data["date"],
            "venue": data["venue"],
            "winner": data["winner"],
            "grid_count": data["grid_count"],
            "result_count": data["result_count"],
            "file": f"/data/bathurst/seasons/{year}.json",
            "source": data["url"],
        })

        print(f"  saved: grid={data['grid_count']} results={data['result_count']}")

    except Exception as e:
        print(f"  FAILED: {e}")

    time.sleep(0.3)

index.sort(key=lambda x: x["year"])

with INDEX_FILE.open("w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print(f"\nDONE: wrote {len(index)} files")
