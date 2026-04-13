import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST WIKIPEDIA BUILDER (MANUAL TABLE PARSER + DRIVER SPLIT + POSITION CLEANUP)")

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
    v = v.replace("†", "")
    v = v.replace("‡", "")
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


def parse_date(value):
    value = clean_text(value)
    if not value:
        return None

    value = value.replace("–", "-")
    value = re.sub(r"\([^)]*\)", "", value).strip()

    candidates = [value]

    if "-" in value:
        parts = [x.strip() for x in value.split("-") if x.strip()]
        candidates.extend(parts[::-1])

    full_dates = re.findall(r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b", value)
    candidates.extend(full_dates)

    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", value)
    if year_match:
        year = year_match.group(1)
        day_month = re.findall(r"\b\d{1,2}\s+[A-Za-z]+\b", value)
        for dm in day_month:
            candidates.append(f"{dm} {year}")

    seen = set()
    ordered = []
    for c in candidates:
        c = clean_text(c)
        if c and c not in seen:
            ordered.append(c)
            seen.add(c)

    for c in ordered:
        for fmt in ("%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y"):
            try:
                return datetime.strptime(c, fmt).strftime("%Y-%m-%d")
            except Exception:
                pass

    return None


def split_drivers(text):
    text = clean_text(text)
    if not text:
        return []

    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace(" and ", " / ")
    text = text.replace(" & ", " / ")
    text = text.replace(" + ", " / ")

    if "/" in text:
        parts = re.split(r"\s*/\s*", text)
        out = []
        seen = set()
        for p in parts:
            p = clean_text(p)
            if not p:
                continue
            low = p.lower()
            if low not in seen:
                out.append(p)
                seen.add(low)
        return out

    # fallback: try to split concatenated full names
    tokens = text.split()
    if len(tokens) == 4:
        # very common early Bathurst format: "Barry Ferguson Bill Ford"
        return [f"{tokens[0]} {tokens[1]}", f"{tokens[2]} {tokens[3]}"]

    names = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z'.-]+)+", text)
    if len(names) >= 2:
        out = []
        seen = set()
        for n in names:
            n = clean_text(n)
            if not n:
                continue
            low = n.lower()
            if low not in seen:
                out.append(n)
                seen.add(low)
        return out

    return [text]


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
                date = parse_date(val)

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


def unique_rows(rows, pos_key):
    out = []
    seen = set()

    for row in rows:
        ident = (
            str(row.get(pos_key)),
            clean_text(row.get("car_no")),
            "|".join(row.get("drivers", [])),
            clean_text(row.get("team")),
            clean_text(row.get("car")),
        )
        if ident in seen:
            continue
        seen.add(ident)
        out.append(row)

    return out


def dedupe_driver_list(drivers):
    out = []
    seen = set()
    for d in drivers:
        d = clean_text(d)
        if not d:
            continue
        low = d.lower()
        if low not in seen:
            out.append(d)
            seen.add(low)
    return out


def guess_driver_cells(row):
    candidates = []

    for cell in row:
        cell = clean_text(cell)
        if not cell:
            continue

        split = split_drivers(cell)
        if len(split) >= 2:
            candidates.extend(split)

    return dedupe_driver_list(candidates)


def parse_manual_results_table(parsed_rows):
    header = [str(x or "").lower() for x in parsed_rows[0]]
    rows = []

    pos_idx = 0
    car_no_idx = None
    driver_idx = None
    team_idx = None
    car_idx = None
    laps_idx = None
    time_idx = None
    gap_idx = None
    status_idx = None

    for i, h in enumerate(header):
        if car_no_idx is None and any(x in h for x in ["car no", "number", "no.", "no", "#"]):
            car_no_idx = i
        if driver_idx is None and "driver" in h:
            driver_idx = i
        if team_idx is None and any(x in h for x in ["team", "entrant"]):
            team_idx = i
        if car_idx is None and any(x in h for x in ["car", "model", "vehicle"]):
            car_idx = i
        if laps_idx is None and "lap" in h:
            laps_idx = i
        if time_idx is None and "time" in h:
            time_idx = i
        if gap_idx is None and "gap" in h:
            gap_idx = i
        if status_idx is None and any(x in h for x in ["status", "reason"]):
            status_idx = i

    for r in parsed_rows[1:]:
        if not r:
            continue

        pos = safe_int(r[pos_idx] if len(r) > pos_idx else None)
        if pos is None:
            continue

        drivers = []
        if driver_idx is not None and len(r) > driver_idx:
            drivers = split_drivers(r[driver_idx])

        if len(drivers) < 2:
            guessed = guess_driver_cells(r)
            if guessed:
                drivers = guessed

        rows.append({
            "finish_pos": pos,
            "car_no": clean_text(r[car_no_idx]) if car_no_idx is not None and len(r) > car_no_idx else None,
            "drivers": dedupe_driver_list(drivers),
            "team": clean_text(r[team_idx]) if team_idx is not None and len(r) > team_idx else None,
            "car": clean_text(r[car_idx]) if car_idx is not None and len(r) > car_idx else None,
            "laps": clean_text(r[laps_idx]) if laps_idx is not None and len(r) > laps_idx else None,
            "time": clean_text(r[time_idx]) if time_idx is not None and len(r) > time_idx else None,
            "gap": clean_text(r[gap_idx]) if gap_idx is not None and len(r) > gap_idx else None,
            "status": clean_text(r[status_idx]) if status_idx is not None and len(r) > status_idx else None,
        })

    rows = unique_rows(rows, "finish_pos")
    rows.sort(key=lambda x: x["finish_pos"])

    # keep only first occurrence of each finish position
    seen_positions = set()
    filtered = []
    for row in rows:
        pos = row["finish_pos"]
        if pos in seen_positions:
            continue
        seen_positions.add(pos)
        filtered.append(row)

    return filtered


def parse_manual_grid_table(parsed_rows):
    header = [str(x or "").lower() for x in parsed_rows[0]]
    rows = []

    pos_idx = 0
    car_no_idx = None
    driver_idx = None
    team_idx = None
    car_idx = None
    time_idx = None

    for i, h in enumerate(header):
        if car_no_idx is None and any(x in h for x in ["car no", "number", "no.", "no", "#"]):
            car_no_idx = i
        if driver_idx is None and "driver" in h:
            driver_idx = i
        if team_idx is None and any(x in h for x in ["team", "entrant"]):
            team_idx = i
        if car_idx is None and any(x in h for x in ["car", "model", "vehicle"]):
            car_idx = i
        if time_idx is None and "time" in h:
            time_idx = i

    for r in parsed_rows[1:]:
        if not r:
            continue

        pos = safe_int(r[pos_idx] if len(r) > pos_idx else None)
        if pos is None:
            continue

        drivers = []
        if driver_idx is not None and len(r) > driver_idx:
            drivers = split_drivers(r[driver_idx])

        if len(drivers) < 2:
            guessed = guess_driver_cells(r)
            if guessed:
                drivers = guessed

        rows.append({
            "grid_pos": pos,
            "car_no": clean_text(r[car_no_idx]) if car_no_idx is not None and len(r) > car_no_idx else None,
            "drivers": dedupe_driver_list(drivers),
            "team": clean_text(r[team_idx]) if team_idx is not None and len(r) > team_idx else None,
            "car": clean_text(r[car_idx]) if car_idx is not None and len(r) > car_idx else None,
            "qualifying_time": clean_text(r[time_idx]) if time_idx is not None and len(r) > time_idx else None,
        })

    rows = unique_rows(rows, "grid_pos")
    rows.sort(key=lambda x: x["grid_pos"])
    return rows


def parse_page(year, url, html):
    soup = BeautifulSoup(html, "html.parser")
    meta = parse_infobox(soup, year, url)

    grid = []
    results = []

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

        if len(rows) < 3:
            continue

        parsed_rows = []

        for tr in rows:
            cols = tr.find_all(["td", "th"])
            if len(cols) < 2:
                continue

            row = [clean_text(c.get_text(" ", strip=True)) for c in cols]
            row = [x for x in row if x is not None]

            if len(row) < 2:
                continue

            parsed_rows.append(row)

        if len(parsed_rows) < 3:
            continue

        heading = get_heading(table)
        flat = " ".join(" ".join(r) for r in parsed_rows).lower()
        first_row = " ".join(parsed_rows[0]).lower()

        is_grid = False
        is_results = False

        if any(x in heading for x in ["starting grid", "grid", "qualifying", "shootout"]):
            is_grid = True

        if any(x in heading for x in ["race", "results", "classification"]):
            is_results = True

        if any(x in first_row for x in ["laps", "gap", "status", "ret", "retired", "time"]):
            is_results = True

        if any(x in first_row for x in ["grid", "qualifying"]):
            is_grid = True

        if not is_results and any(x in flat for x in ["laps", "gap", "retired", "classification"]):
            is_results = True

        if not is_grid and any(x in flat for x in ["starting grid", "qualifying order", "pole time"]):
            is_grid = True

        data_rows_with_numeric_first_cell = 0
        for r in parsed_rows[1:]:
            if safe_int(r[0]) is not None:
                data_rows_with_numeric_first_cell += 1

        if not is_results and not is_grid and data_rows_with_numeric_first_cell >= 10:
            is_results = True

        if is_results:
            candidate = parse_manual_results_table(parsed_rows)
            if len(candidate) > len(results):
                results = candidate
            continue

        if is_grid:
            candidate = parse_manual_grid_table(parsed_rows)
            if len(candidate) > len(grid):
                grid = candidate
            continue

    winner = []
    for r in results:
        if r["finish_pos"] == 1:
            winner = r["drivers"]
            break

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

        out_file = SEASONS_DIR / f"{year}.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        index.append({
            "year": data["year"],
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
