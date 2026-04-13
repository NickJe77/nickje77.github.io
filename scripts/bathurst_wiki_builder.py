import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote

import pandas as pd
import requests
from bs4 import BeautifulSoup

print("BATHURST WIKIPEDIA BUILDER (MASTER INDEX + GRID + RESULTS)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1960
END_YEAR = datetime.utcnow().year

WIKI_BASE = "https://en.wikipedia.org"
WIKI_PAGE_BASE = "https://en.wikipedia.org/wiki/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BathurstBuilder/1.0; +https://nickje77.github.io/)"
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# --------------------------------------------------
# helpers
# --------------------------------------------------
def clean_text(value):
    if value is None:
        return None
    value = str(value)
    value = re.sub(r"\[[^\]]*\]", "", value)
    value = value.replace("\xa0", " ")
    value = value.replace("†", "")
    value = value.replace("‡", "")
    value = value.replace("\u200b", "")
    value = re.sub(r"\s+", " ", value).strip()
    return value if value else None


def slugify(value):
    value = clean_text(value) or ""
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def safe_int(value):
    if value is None:
        return None
    value = clean_text(value)
    if not value:
        return None
    m = re.search(r"\d+", value)
    return int(m.group()) if m else None


def parse_date_text(text):
    text = clean_text(text)
    if not text:
        return None

    text = re.sub(r"\([^)]*\)", "", text).strip()
    text = text.replace("–", "-")
    text = re.sub(r"\s+", " ", text)

    patterns = [
        "%d %B %Y",
        "%B %d %Y",
        "%d %b %Y",
        "%b %d %Y",
    ]

    exact_candidates = [text]

    # handle date ranges
    if "-" in text:
        parts = [x.strip() for x in text.split("-") if x.strip()]
        exact_candidates.extend(parts[::-1])

    # extract full dates inside text
    exact_candidates.extend(re.findall(r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b", text))

    # handle "2 October" + year elsewhere
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if year_match:
        year = year_match.group(1)
        dm = re.findall(r"\b\d{1,2}\s+[A-Za-z]+\b", text)
        for x in dm:
            exact_candidates.append(f"{x} {year}")

    seen = set()
    ordered = []
    for c in exact_candidates:
        c = clean_text(c)
        if c and c not in seen:
            ordered.append(c)
            seen.add(c)

    for candidate in ordered:
        for fmt in patterns:
            try:
                return datetime.strptime(candidate, fmt).strftime("%Y-%m-%d")
            except Exception:
                pass

    return None


def fetch_html(url):
    try:
        r = SESSION.get(url, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def normalize_columns(df):
    cols = []
    for i, c in enumerate(df.columns):
        if isinstance(c, tuple):
            c = " ".join([str(x) for x in c if str(x) != "nan"])
        c = clean_text(c)
        cols.append(c or f"col_{i+1}")
    df = df.copy()
    df.columns = cols
    return df


def dedupe_preserve(items):
    out = []
    seen = set()
    for x in items:
        k = (x or "").lower()
        if k and k not in seen:
            out.append(x)
            seen.add(k)
    return out


def split_drivers(text):
    text = clean_text(text)
    if not text:
        return []

    text = re.sub(r"\(.*?\)", "", text)
    text = text.replace(" / ", "/")
    text = text.replace(" & ", " / ")
    text = text.replace(" and ", " / ")
    text = text.replace(" + ", " / ")
    text = re.sub(r"\s*/\s*", " / ", text)

    parts = [clean_text(x) for x in text.split(" / ") if clean_text(x)]

    cleaned = []
    for p in parts:
        p = re.sub(r"\b(?:Driver|Drivers|Co-driver|Codriver|Co driver)\b", "", p, flags=re.I)
        p = clean_text(p)
        if not p:
            continue
        if len(p) <= 2:
            continue
        cleaned.append(p)

    return dedupe_preserve(cleaned)


def get_heading_for_table(table_tag):
    node = table_tag
    while True:
        node = node.find_previous(["h2", "h3", "h4"])
        if not node:
            return ""
        text = clean_text(node.get_text(" ", strip=True)) or ""
        text = text.replace("[edit]", "").strip()
        if text:
            return text.lower()


def get_infobox_value(soup, wanted_keys):
    infobox = soup.find("table", class_=lambda c: c and "infobox" in c)
    if not infobox:
        return None

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
        if any(w in low for w in wanted_keys):
            return val
    return None


# --------------------------------------------------
# year -> page map from main Bathurst page
# --------------------------------------------------
def build_year_page_map():
    print("Building year map from Bathurst 1000 page...")

    html = fetch_html("https://en.wikipedia.org/wiki/Bathurst_1000")
    if not html:
        raise RuntimeError("Could not load main Bathurst 1000 page")

    soup = BeautifulSoup(html, "html.parser")
    year_map = {}

    for table in soup.find_all("table", class_="wikitable"):
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if not tds:
                continue

            for td in tds:
                links = td.find_all("a", href=True)
                for a in links:
                    label = clean_text(a.get_text(" ", strip=True))
                    href = a.get("href", "")
                    if not label or not href.startswith("/wiki/"):
                        continue

                    # direct year link text
                    if re.fullmatch(r"(19\d{2}|20\d{2})", label):
                        year = int(label)
                        year_map[year] = {
                            "title": label,
                            "url": WIKI_BASE + href
                        }
                        continue

                    # linked article title / href contains year and likely Bathurst page name
                    full_text = f"{label} {unquote(href)}".lower()
                    m = re.search(r"\b(19\d{2}|20\d{2})\b", full_text)
                    if not m:
                        continue

                    year = int(m.group(1))
                    if any(x in full_text for x in [
                        "bathurst", "gallaher", "armstrong", "hardie",
                        "tooheys", "fai", "supercheap", "repco", "great race"
                    ]):
                        year_map[year] = {
                            "title": label,
                            "url": WIKI_BASE + href
                        }

    # patch obvious missing years with conventional titles
    manual_candidates = {
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

    for year in range(START_YEAR, END_YEAR + 1):
        if year not in year_map and year in manual_candidates:
            slug = manual_candidates[year]
            year_map[year] = {
                "title": slug.replace("_", " "),
                "url": WIKI_PAGE_BASE + quote(slug)
            }

    print(f"Mapped {len(year_map)} years")
    return year_map


# --------------------------------------------------
# table classification
# --------------------------------------------------
def classify_table(df, heading):
    heading = (heading or "").lower()
    cols = " | ".join([str(c).lower() for c in df.columns])

    grid_score = 0
    result_score = 0

    if any(x in heading for x in ["starting grid", "grid", "qualifying", "top ten shootout"]):
        grid_score += 5
    if any(x in heading for x in ["race results", "race", "results", "classification", "classified"]):
        result_score += 5

    if any(x in cols for x in ["grid", "qualifying", "time"]):
        grid_score += 1

    if any(x in cols for x in ["laps", "lap", "gap", "status", "ret", "retired"]):
        result_score += 2

    if any(x in cols for x in ["driver", "co-driver", "team", "car", "no.", "number", "position", "pos"]):
        grid_score += 1
        result_score += 1

    if "laps" in cols or "status" in cols or "gap" in cols:
        result_score += 2

    if "grid" in heading or "qualifying" in heading:
        return "grid"
    if "race" in heading or "classification" in heading:
        return "results"

    if result_score > grid_score and result_score >= 3:
        return "results"
    if grid_score > result_score and grid_score >= 3:
        return "grid"

    return None


# --------------------------------------------------
# row extraction
# --------------------------------------------------
def pick_first(keys, needles):
    for needle in needles:
        for k, v in keys.items():
            if needle in k:
                return clean_text(v)
    return None


def extract_drivers_from_record(record):
    keys = {str(k).lower(): v for k, v in record.items()}
    drivers = []

    driver = pick_first(keys, ["driver"])
    co_driver = pick_first(keys, ["co-driver", "co driver", "codriver"])

    if driver:
        drivers.extend(split_drivers(driver))
    if co_driver:
        drivers.extend(split_drivers(co_driver))

    if not drivers:
        for k, v in keys.items():
            if "driver" in k or "crew" in k:
                x = split_drivers(v)
                if x:
                    drivers.extend(x)

    if not drivers:
        for k, v in keys.items():
            txt = clean_text(v)
            if not txt:
                continue
            if "/" in txt and re.search(r"[A-Z][a-z]+", txt):
                x = split_drivers(txt)
                if x:
                    drivers.extend(x)
                    break

    return dedupe_preserve(drivers)


def extract_common_fields(record):
    keys = {str(k).lower(): v for k, v in record.items()}

    return {
        "position": pick_first(keys, ["position", "pos", "place"]),
        "car_no": pick_first(keys, ["car no", "number", "no.", "no", "#"]),
        "team": pick_first(keys, ["team", "entrant"]),
        "car": pick_first(keys, ["car", "vehicle", "make/model", "model"]),
        "qualifying_time": pick_first(keys, ["qualifying time", "time"]),
        "laps": pick_first(keys, ["laps", "lap"]),
        "race_time": pick_first(keys, ["total time", "race time", "time"]),
        "gap": pick_first(keys, ["gap"]),
        "status": pick_first(keys, ["status", "reason"]),
        "class": pick_first(keys, ["class"]),
    }


def normalize_grid_rows(records):
    out = []
    for record in records:
        common = extract_common_fields(record)
        pos = safe_int(common["position"])
        drivers = extract_drivers_from_record(record)

        if pos is None:
            continue

        out.append({
            "grid_pos": pos,
            "car_no": common["car_no"],
            "drivers": drivers,
            "team": common["team"],
            "car": common["car"],
            "qualifying_time": common["qualifying_time"],
        })
    return out


def normalize_result_rows(records):
    out = []
    for record in records:
        common = extract_common_fields(record)
        drivers = extract_drivers_from_record(record)

        pos_raw = common["position"]
        pos_int = safe_int(pos_raw)

        if pos_raw is None and not drivers and not common["car"]:
            continue

        out.append({
            "finish_pos": pos_int if pos_int is not None else pos_raw,
            "car_no": common["car_no"],
            "drivers": drivers,
            "team": common["team"],
            "car": common["car"],
            "laps": common["laps"],
            "time": common["race_time"],
            "gap": common["gap"],
            "status": common["status"],
            "class": common["class"],
        })
    return out


def cleanup_grid(rows):
    out = []
    seen = set()

    for row in rows:
        row = dict(row)
        row["car_no"] = clean_text(row.get("car_no"))
        row["team"] = clean_text(row.get("team"))
        row["car"] = clean_text(row.get("car"))
        row["qualifying_time"] = clean_text(row.get("qualifying_time"))
        row["drivers"] = dedupe_preserve([clean_text(x) for x in row.get("drivers", []) if clean_text(x)])

        ident = (
            row.get("grid_pos"),
            row.get("car_no"),
            "|".join(row.get("drivers", [])),
            row.get("car"),
        )
        if ident in seen:
            continue
        seen.add(ident)
        out.append(row)

    out.sort(key=lambda x: (x.get("grid_pos") or 9999))
    return out


def cleanup_results(rows):
    out = []
    seen = set()

    for row in rows:
        row = dict(row)
        row["car_no"] = clean_text(row.get("car_no"))
        row["team"] = clean_text(row.get("team"))
        row["car"] = clean_text(row.get("car"))
        row["laps"] = clean_text(row.get("laps"))
        row["time"] = clean_text(row.get("time"))
        row["gap"] = clean_text(row.get("gap"))
        row["status"] = clean_text(row.get("status"))
        row["class"] = clean_text(row.get("class"))
        row["drivers"] = dedupe_preserve([clean_text(x) for x in row.get("drivers", []) if clean_text(x)])

        ident = (
            str(row.get("finish_pos")),
            row.get("car_no"),
            "|".join(row.get("drivers", [])),
            row.get("car"),
        )
        if ident in seen:
            continue
        seen.add(ident)
        out.append(row)

    def sort_key(x):
        v = x.get("finish_pos")
        if isinstance(v, int):
            return (0, v)
        if isinstance(v, str):
            m = re.search(r"\d+", v)
            if m:
                return (0, int(m.group()))
        return (1, 9999)

    out.sort(key=sort_key)
    return out


# --------------------------------------------------
# fallbacks for winner / metadata
# --------------------------------------------------
def infer_winner_from_intro(soup):
    text = clean_text(soup.get_text(" ", strip=True)) or ""
    m = re.search(
        r"won by ([A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+)+(?:\s*/\s*[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+)+)?)",
        text
    )
    if m:
        return split_drivers(m.group(1))
    return []


def fill_missing_drivers_from_nearby_text(table_tag, rows, key_name):
    if not rows:
        return rows

    text_blob = clean_text(table_tag.get_text(" ", strip=True)) or ""
    possible_pairs = re.findall(
        r"([A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+)+\s*/\s*[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+)+)",
        text_blob
    )
    possible_pairs = [split_drivers(x) for x in possible_pairs if split_drivers(x)]

    if not possible_pairs:
        return rows

    fixed = []
    for row in rows:
        row = dict(row)
        if len(row.get("drivers", [])) >= 2:
            fixed.append(row)
            continue

        for pair in possible_pairs:
            if len(pair) >= 2:
                row["drivers"] = pair
                break

        fixed.append(row)

    return fixed


# --------------------------------------------------
# parse one page
# --------------------------------------------------
def parse_page(year, title, url, html):
    soup = BeautifulSoup(html, "html.parser")

    page_title = clean_text(soup.find("h1").get_text(" ", strip=True)) if soup.find("h1") else clean_text(title)
    race_name = get_infobox_value(soup, ["race", "event", "name"]) or page_title
    date = parse_date_text(get_infobox_value(soup, ["date"]) or "")
    venue = get_infobox_value(soup, ["location", "venue", "circuit"])

    grid = []
    results = []

    for table_tag in soup.find_all("table", class_=lambda c: c and "wikitable" in c):
        heading = get_heading_for_table(table_tag)

        dfs = []
        try:
            dfs = pd.read_html(str(table_tag))
        except Exception:
            dfs = []

        for df in dfs:
            try:
                df = normalize_columns(df)
                kind = classify_table(df, heading)
                if not kind:
                    continue

                records = df.fillna("").to_dict(orient="records")

                if kind == "grid":
                    candidate = normalize_grid_rows(records)
                    candidate = fill_missing_drivers_from_nearby_text(table_tag, candidate, "grid_pos")
                    if len(candidate) > len(grid):
                        grid = candidate

                elif kind == "results":
                    candidate = normalize_result_rows(records)
                    candidate = fill_missing_drivers_from_nearby_text(table_tag, candidate, "finish_pos")
                    if len(candidate) > len(results):
                        results = candidate
            except Exception:
                pass

    grid = cleanup_grid(grid)
    results = cleanup_results(results)

    winner = results[0]["drivers"] if results and results[0].get("drivers") else infer_winner_from_intro(soup)

    return {
        "year": year,
        "title": page_title,
        "name": race_name,
        "date": date,
        "venue": venue,
        "url": url,
        "winner": winner,
        "grid_count": len(grid),
        "result_count": len(results),
        "grid": grid,
        "results": results,
    }


# --------------------------------------------------
# build
# --------------------------------------------------
YEAR_MAP = build_year_page_map()
index = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    info = YEAR_MAP.get(year)
    if not info:
        print("  No page mapping found")
        continue

    url = info["url"]
    html = fetch_html(url)

    if not html:
        print(f"  Could not load page: {url}")
        continue

    try:
        data = parse_page(year, info["title"], url, html)

        if not data["grid"] and not data["results"]:
            print("  No usable grid/results found")
            continue

        out_file = SEASONS_DIR / f"{year}.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        index.append({
            "year": year,
            "title": data.get("title"),
            "name": data.get("name"),
            "date": data.get("date"),
            "venue": data.get("venue"),
            "winner": data.get("winner", []),
            "grid_count": data.get("grid_count", 0),
            "result_count": data.get("result_count", 0),
            "file": f"/data/bathurst/seasons/{year}.json",
            "source": data.get("url"),
        })

        print(
            f"  Saved {year}.json "
            f"(grid={data['grid_count']}, results={data['result_count']})"
        )

    except Exception as e:
        print(f"  FAILED {year}: {e}")

    time.sleep(0.4)

index.sort(key=lambda x: x["year"])

with INDEX_FILE.open("w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print(f"\nDONE: wrote {len(index)} season files")
print(f"Index: {INDEX_FILE}")
