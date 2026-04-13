import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup

print("BATHURST WIKIPEDIA SCRAPER (GRID + RESULTS)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1960
END_YEAR = datetime.utcnow().year

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BathurstBuilder/1.0; +https://en.wikipedia.org/)"
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_BASE = "https://en.wikipedia.org/wiki/"


# -----------------------------
# Basic helpers
# -----------------------------
def clean_text(value):
    if value is None:
        return None
    value = str(value)
    value = re.sub(r"\[[^\]]*\]", "", value)   # refs [1]
    value = value.replace("\xa0", " ")
    value = value.replace("†", "")
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


def table_to_records(table_tag):
    rows = table_tag.find_all("tr")
    if not rows:
        return []

    header = []
    records = []

    for tr in rows:
        ths = tr.find_all("th")
        tds = tr.find_all("td")

        if ths and not tds:
            header = [clean_text(x.get_text(" ", strip=True)) for x in ths]
            continue

        if tds:
            vals = [clean_text(x.get_text(" ", strip=True)) for x in tds]
            if header and len(vals) == len(header):
                records.append(dict(zip(header, vals)))
            else:
                # fallback when header widths do not match
                records.append({f"col_{i+1}": v for i, v in enumerate(vals)})

    return records


def get_heading_for_table(table_tag):
    node = table_tag
    while node:
        node = node.find_previous(["h2", "h3", "h4"])
        if not node:
            return ""
        text = clean_text(node.get_text(" ", strip=True)) or ""
        text = text.replace("[edit]", "").strip()
        if text:
            return text.lower()
    return ""


def normalize_columns(df):
    df = df.copy()
    df.columns = [clean_text(c) or f"col_{i+1}" for i, c in enumerate(df.columns)]
    return df


def best_col(columns, choices):
    norm = {c.lower(): c for c in columns}
    for choice in choices:
        for low, orig in norm.items():
            if choice in low:
                return orig
    return None


def split_drivers(text):
    if not text:
        return []

    text = clean_text(text)
    if not text:
        return []

    # common separators seen on wiki / motorsport pages
    parts = re.split(
        r"\s*/\s*|\s+\band\b\s+|\s*&\s*|\s+\+\s+|\s*,\s*(?=[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        text,
        flags=re.I,
    )
    parts = [clean_text(p) for p in parts if clean_text(p)]

    cleaned = []
    for p in parts:
        p = re.sub(r"\(.*?\)", "", p).strip()
        p = clean_text(p)
        if p and p.lower() not in {"driver", "co-driver", "drivers"}:
            cleaned.append(p)

    # de-dup while preserving order
    out = []
    seen = set()
    for x in cleaned:
        k = x.lower()
        if k not in seen:
            out.append(x)
            seen.add(k)

    return out


def parse_date_text(text):
    text = clean_text(text)
    if not text:
        return None

    text = re.sub(r"\([^)]*\)", "", text).strip()
    text = re.sub(r"\s+", " ", text)

    patterns = [
        "%d %B %Y",
        "%B %d %Y",
        "%d %b %Y",
        "%b %d %Y",
    ]

    # handle ranges like "1 October 1967" or "30 September – 2 October 1967"
    text = text.replace("–", "-")
    if "-" in text:
        bits = [b.strip() for b in text.split("-")]
        text = bits[-1]

    # try exact
    for fmt in patterns:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass

    # pull last full date from the string
    m = re.findall(r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b", text)
    if m:
        for candidate in reversed(m):
            for fmt in patterns:
                try:
                    return datetime.strptime(candidate, fmt).strftime("%Y-%m-%d")
                except Exception:
                    pass

    return None


# -----------------------------
# Wikipedia page discovery
# -----------------------------
def search_wikipedia_titles(query):
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 10,
    }
    try:
        r = SESSION.get(WIKI_API, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        return [x["title"] for x in data.get("query", {}).get("search", [])]
    except Exception:
        return []


def get_page_html(title):
    url = WIKI_BASE + quote(title.replace(" ", "_"))
    r = SESSION.get(url, timeout=30)
    if r.status_code != 200 or "Wikipedia does not have an article with this exact name" in r.text:
        return None, None
    return url, r.text


def find_bathurst_page_for_year(year):
    queries = [
        f"{year} Bathurst 1000",
        f"{year} Bathurst race",
        f"{year} Bathurst",
        f"{year} Gallaher 500",
        f"{year} Armstrong 500",
        f"{year} Hardie-Ferodo 1000",
        f"{year} James Hardie 1000",
        f"{year} Tooheys 1000",
        f"{year} Supercheap Auto Bathurst 1000",
        f"{year} Repco Bathurst 1000",
    ]

    seen = set()
    candidates = []

    for q in queries:
        for title in search_wikipedia_titles(q):
            t = clean_text(title)
            if not t:
                continue
            low = t.lower()
            if str(year) not in low:
                continue
            if "bathurst" in low or "gallaher 500" in low or "armstrong 500" in low or "hardie" in low or "tooheys 1000" in low:
                if t not in seen:
                    seen.add(t)
                    candidates.append(t)

    # strong preference for likely main-event pages
    def score(title):
        low = title.lower()
        s = 0
        if str(year) in low:
            s += 10
        if "bathurst" in low:
            s += 20
        if "1000" in low or "500" in low:
            s += 10
        if "armstrong" in low or "gallaher" in low or "hardie" in low or "tooheys" in low or "supercheap" in low or "repco" in low:
            s += 8
        if "support" in low or "shootout" in low or "qualifying" in low:
            s -= 25
        return -s

    candidates.sort(key=score)

    for title in candidates:
        url, html = get_page_html(title)
        if not html:
            continue
        if "Mount Panorama" in html or "Bathurst" in html:
            return title, url, html

    return None, None, None


# -----------------------------
# Infobox / summary extraction
# -----------------------------
def parse_infobox(soup, year, title, url):
    data = {
        "year": year,
        "title": clean_text(title),
        "url": url,
        "date": None,
        "venue": None,
        "name": clean_text(title),
    }

    infobox = soup.find("table", class_=lambda c: c and "infobox" in c)
    if not infobox:
        return data

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

        if low == "date" and not data["date"]:
            data["date"] = parse_date_text(val)

        elif low in {"location", "venue"} and not data["venue"]:
            data["venue"] = val

        elif low in {"race", "event", "name"} and val:
            data["name"] = val

    return data


# -----------------------------
# Table classification
# -----------------------------
def classify_table(df, heading):
    cols = [str(c).lower() for c in df.columns]
    heading = (heading or "").lower()
    col_blob = " | ".join(cols)

    grid_score = 0
    result_score = 0

    if any(x in heading for x in ["grid", "starting grid", "qualifying", "top ten shootout"]):
        grid_score += 5
    if any(x in heading for x in ["race", "race results", "results", "classification", "classified"]):
        result_score += 5

    if any(x in col_blob for x in ["grid", "qualifying", "time"]):
        grid_score += 1
    if any(x in col_blob for x in ["laps", "status", "time", "gap", "ret", "retired"]):
        result_score += 2

    if any(x in col_blob for x in ["pos", "position", "no.", "car", "driver", "co-driver", "team"]):
        grid_score += 1
        result_score += 1

    if "laps" in col_blob or "status" in col_blob:
        result_score += 2

    if "qualifying" in heading or "grid" in heading:
        return "grid"
    if "race" in heading or "classification" in heading or "results" in heading:
        return "results"

    if result_score > grid_score and result_score >= 3:
        return "results"
    if grid_score > result_score and grid_score >= 3:
        return "grid"

    return None


# -----------------------------
# Row parsing
# -----------------------------
def extract_drivers_from_row(row):
    keys = {str(k).lower(): v for k, v in row.items()}

    # separate driver columns
    driver = None
    codriver = None

    for k, v in keys.items():
        if "co-driver" in k or "codriver" in k or "co driver" in k:
            codriver = v
        elif k == "driver" or "driver 1" in k or ("driver" in k and "co" not in k):
            driver = v

    drivers = []
    if driver:
        drivers.extend(split_drivers(driver))
    if codriver:
        drivers.extend(split_drivers(codriver))

    # combined driver columns
    if not drivers:
        for k, v in keys.items():
            if "driver" in k or "crew" in k:
                drivers = split_drivers(v)
                if drivers:
                    break

    # if nothing obvious, sometimes names are in one of the generic columns
    if not drivers:
        for k, v in keys.items():
            txt = clean_text(v)
            if not txt:
                continue
            # crude name pattern: at least two capitalised words, with possible slash
            if re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z'.-]+)+", txt):
                possible = split_drivers(txt)
                if 1 <= len(possible) <= 4:
                    drivers = possible
                    break

    # dedupe
    out = []
    seen = set()
    for d in drivers:
        low = d.lower()
        if low not in seen:
            out.append(d)
            seen.add(low)

    return out


def extract_common_fields(row):
    keys = {str(k).lower(): v for k, v in row.items()}

    def pick(possible):
        for needle in possible:
            for k, v in keys.items():
                if needle in k:
                    return clean_text(v)
        return None

    return {
        "position": pick(["position", "pos", "place"]),
        "car_no": pick(["car no", "number", "no.", "no", "#"]),
        "team": pick(["team", "entrant"]),
        "car": pick(["car", "vehicle", "make/model", "model"]),
        "qualifying_time": pick(["qualifying time", "time"]),
        "laps": pick(["laps"]),
        "race_time": pick(["total time", "time"]),
        "gap": pick(["gap"]),
        "status": pick(["status", "reason"]),
        "class": pick(["class"]),
    }


def normalize_grid_rows(records):
    out = []

    for row in records:
        common = extract_common_fields(row)
        drivers = extract_drivers_from_row(row)

        pos = safe_int(common["position"])
        if pos is None:
            # skip obviously invalid rows
            continue

        item = {
            "grid_pos": pos,
            "car_no": common["car_no"],
            "drivers": drivers,
            "team": common["team"],
            "car": common["car"],
            "qualifying_time": common["qualifying_time"],
        }

        out.append(item)

    return out


def normalize_result_rows(records):
    out = []

    for row in records:
        common = extract_common_fields(row)
        drivers = extract_drivers_from_row(row)

        pos_raw = common["position"]
        pos = safe_int(pos_raw)

        if pos is None and not pos_raw:
            continue

        item = {
            "finish_pos": pos_raw,
            "car_no": common["car_no"],
            "drivers": drivers,
            "team": common["team"],
            "car": common["car"],
            "laps": common["laps"],
            "time": common["race_time"],
            "gap": common["gap"],
            "status": common["status"],
            "class": common["class"],
        }

        out.append(item)

    return out


def fallback_from_wikitext_rows(rows):
    """
    Fallback for odd wiki tables where pandas misreads headers.
    """
    out = []
    for r in rows:
        row = {clean_text(k): clean_text(v) for k, v in r.items()}
        if not row:
            continue
        out.append(row)
    return out


# -----------------------------
# Main page parser
# -----------------------------
def parse_bathurst_page(year, title, url, html):
    soup = BeautifulSoup(html, "html.parser")
    meta = parse_infobox(soup, year, title, url)

    tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)
    grid = []
    results = []

    for table_tag in tables:
        heading = get_heading_for_table(table_tag)

        # first try pandas for better rowspan handling
        dfs = []
        try:
            dfs = pd.read_html(str(table_tag))
        except Exception:
            dfs = []

        classified = False

        for df in dfs:
            try:
                df = normalize_columns(df)
                kind = classify_table(df, heading)
                if not kind:
                    continue

                records = df.fillna("").to_dict(orient="records")

                if kind == "grid":
                    rows = normalize_grid_rows(records)
                    if len(rows) > len(grid):
                        grid = rows
                        classified = True

                elif kind == "results":
                    rows = normalize_result_rows(records)
                    if len(rows) > len(results):
                        results = rows
                        classified = True
            except Exception:
                pass

        # fallback parser if pandas did not classify it
        if not classified:
            raw_records = fallback_from_wikitext_rows(table_to_records(table_tag))
            if raw_records:
                df = pd.DataFrame(raw_records)
                if not df.empty:
                    df = normalize_columns(df)
                    kind = classify_table(df, heading)
                    if kind == "grid":
                        rows = normalize_grid_rows(df.fillna("").to_dict(orient="records"))
                        if len(rows) > len(grid):
                            grid = rows
                    elif kind == "results":
                        rows = normalize_result_rows(df.fillna("").to_dict(orient="records"))
                        if len(rows) > len(results):
                            results = rows

    # basic cleanup / fill
    meta["grid"] = grid
    meta["results"] = results
    meta["winner"] = results[0]["drivers"] if results else []
    meta["grid_count"] = len(grid)
    meta["result_count"] = len(results)

    return meta


# -----------------------------
# Validation / cleanup
# -----------------------------
def cleanup_rows(rows, key_name):
    cleaned = []
    seen = set()

    for row in rows:
        row = dict(row)

        if key_name in row and isinstance(row[key_name], str):
            row[key_name] = clean_text(row[key_name])

        if "car_no" in row:
            row["car_no"] = clean_text(row["car_no"])

        if "team" in row:
            row["team"] = clean_text(row["team"])

        if "car" in row:
            row["car"] = clean_text(row["car"])

        if "drivers" in row and isinstance(row["drivers"], list):
            row["drivers"] = [clean_text(x) for x in row["drivers"] if clean_text(x)]

        ident = (
            str(row.get(key_name)),
            str(row.get("car_no")),
            "|".join(row.get("drivers", [])),
            str(row.get("car")),
        )
        if ident in seen:
            continue
        seen.add(ident)
        cleaned.append(row)

    return cleaned


# -----------------------------
# Run build
# -----------------------------
index = []

for year in range(START_YEAR, END_YEAR + 1):
    try:
        print(f"\n=== {year} ===")

        title, url, html = find_bathurst_page_for_year(year)
        if not html:
            print(f"  No page found for {year}")
            continue

        data = parse_bathurst_page(year, title, url, html)
        data["grid"] = cleanup_rows(data.get("grid", []), "grid_pos")
        data["results"] = cleanup_rows(data.get("results", []), "finish_pos")

        # only save if we found at least something useful
        if not data["grid"] and not data["results"]:
            print(f"  Found page but no usable grid/results for {year}: {title}")
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
            "grid_count": len(data.get("grid", [])),
            "result_count": len(data.get("results", [])),
            "file": f"/data/bathurst/seasons/{year}.json",
            "source": data.get("url"),
        })

        print(
            f"  Saved {year}: "
            f"grid={len(data.get('grid', []))}, "
            f"results={len(data.get('results', []))}, "
            f"title={data.get('title')}"
        )

        time.sleep(0.5)

    except Exception as e:
        print(f"  FAILED {year}: {e}")

index.sort(key=lambda x: x["year"])

with INDEX_FILE.open("w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print(f"\nDone. Saved {len(index)} seasons to {SEASONS_DIR}")
print(f"Index written to {INDEX_FILE}")
