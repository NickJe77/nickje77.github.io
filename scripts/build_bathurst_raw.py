import csv
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("BUILDING BATHURST RAW (HEADER-BASED)")

OUT = Path("docs/data/bathurst/raw/bathurst_full.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if x is None:
        return ""
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x


def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500",
        f"{year}_Tooheys_1000",
        f"{year}_James_Hardie_1000",
        f"{year}_AMP_Bathurst_1000",
    ]

    for p in patterns:
        url = f"https://en.wikipedia.org/wiki/{p}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return url
        except Exception:
            pass

    return None


def find_results_table(soup):
    candidates = []

    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True).lower()
        score = 0

        if "driver" in text or "drivers" in text:
            score += 3
        if "pos" in text or "position" in text:
            score += 3
        if "car" in text or "make" in text or "model" in text:
            score += 2
        if "class" in text:
            score -= 1

        if score >= 5:
            candidates.append((score, table))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def get_table_rows(table):
    return table.find_all("tr")


def row_cells(tr):
    return tr.find_all(["th", "td"])


def build_header_map(table):
    """
    Returns a dict: column index -> normalized header text
    using the last header row before the data rows start.
    """
    rows = get_table_rows(table)
    header_rows = []

    for tr in rows:
        cells = row_cells(tr)
        if not cells:
            continue

        has_td = any(c.name == "td" for c in cells)
        if has_td:
            break

        header_rows.append(tr)

    if not header_rows:
        # fallback: use first row even if mixed
        first = rows[0] if rows else None
        if not first:
            return {}
        cells = row_cells(first)
        return {i: clean(c.get_text(" ", strip=True)).lower() for i, c in enumerate(cells)}

    header_tr = header_rows[-1]
    cells = row_cells(header_tr)
    return {i: clean(c.get_text(" ", strip=True)).lower() for i, c in enumerate(cells)}


def find_col(header_map, keywords):
    for idx, name in header_map.items():
        for kw in keywords:
            if kw in name:
                return idx
    return None


def looks_like_person(name):
    name = clean(name)
    if not name:
        return False
    if any(ch.isdigit() for ch in name):
        return False

    bad_terms = {
        "ford", "holden", "morris", "volkswagen", "vw", "simca", "triumph",
        "mini", "cortina", "falcon", "torana", "commodore", "nissan",
        "mazda", "toyota", "bmw", "porsche", "mercedes", "audi",
        "motors", "motor", "sales", "ltd", "pty", "co", "team",
        "racing", "engineering", "agents", "dealer", "dealers",
        "herald", "aronde", "elite", "valiant", "cooper"
    }

    lower = name.lower()
    tokens = lower.split()

    if len(tokens) < 2 or len(tokens) > 4:
        return False

    if any(tok in bad_terms for tok in tokens):
        return False

    # allow initials like "J. Smith" or "A Brown"
    original_tokens = name.split()
    good_parts = 0
    for tok in original_tokens:
        tok = tok.strip(".")
        if re.fullmatch(r"[A-Z]", tok):
            good_parts += 1
            continue
        if re.fullmatch(r"[A-Z][a-z'`-]+", tok):
            good_parts += 1
            continue
    return good_parts >= 2


def extract_driver_names_from_cell(td):
    names = []

    for a in td.find_all("a"):
        text = clean(a.get_text(" ", strip=True))
        if looks_like_person(text) and text not in names:
            names.append(text)

    if len(names) >= 2:
        return names[:2]

    # fallback from plain text split
    raw = clean(td.get_text(" ", strip=True))
    parts = re.split(r"\s*/\s*|\s*&\s*|\s+and\s+|\s*,\s*", raw)

    for part in parts:
        part = clean(part)
        if looks_like_person(part) and part not in names:
            names.append(part)

    return names[:2]


def parse_finish_from_row(tr):
    cells = row_cells(tr)
    if not cells:
        return None

    first = clean(cells[0].get_text(" ", strip=True))
    if first.isdigit():
        return int(first)

    # fallback: first td/th in row containing just a number
    for c in cells:
        txt = clean(c.get_text(" ", strip=True))
        if txt.isdigit():
            return int(txt)

    return None


def get_cell_by_index(tds, idx):
    if idx is None:
        return None
    if 0 <= idx < len(tds):
        return tds[idx]
    return None


def pick_car_text(tds, header_map, driver_idx):
    # Prefer explicit car columns from header
    preferred = [
        find_col(header_map, ["car"]),
        find_col(header_map, ["make"]),
        find_col(header_map, ["model"]),
        find_col(header_map, ["vehicle"]),
    ]

    for idx in preferred:
        td = get_cell_by_index(tds, idx)
        if td:
            txt = clean(td.get_text(" ", strip=True))
            if txt:
                return txt

    # fallback: first non-driver, non-position cell that looks car-like
    for i, td in enumerate(tds):
        if i == driver_idx:
            continue

        txt = clean(td.get_text(" ", strip=True))
        if not txt:
            continue
        if txt.isdigit():
            continue

        lower = txt.lower()
        if any(term in lower for term in [
            "ford", "holden", "morris", "volkswagen", "vw", "simca", "triumph",
            "mini", "cortina", "falcon", "torana", "commodore", "nissan",
            "mazda", "toyota", "bmw", "porsche", "mercedes", "audi",
            "herald", "aronde", "elite", "valiant", "cooper"
        ]):
            return txt

    return ""


def parse_year(year):
    url = get_url(year)
    if not url:
        print(f"❌ No page {year}")
        return []

    print(f"Fetching {year} -> {url}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        res.raise_for_status()
    except Exception:
        print(f"❌ Request failed {year}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    table = find_results_table(soup)

    if not table:
        print(f"❌ No results table {year}")
        return []

    header_map = build_header_map(table)

    driver_idx = find_col(header_map, ["driver", "drivers"])
    pos_idx = find_col(header_map, ["pos", "position"])
    # pos_idx is not essential because parse_finish_from_row is more robust

    rows = []
    by_finish = {}

    for tr in get_table_rows(table):
        tds = tr.find_all("td")
        if not tds:
            continue

        finish = parse_finish_from_row(tr)
        if finish is None:
            continue

        if finish <= 0 or finish > 80:
            continue

        drivers = []

        if driver_idx is not None and driver_idx < len(tds):
            drivers = extract_driver_names_from_cell(tds[driver_idx])

        if len(drivers) < 2:
            # fallback: find best cell in row
            best = []
            best_idx = None
            for i, td in enumerate(tds):
                cand = extract_driver_names_from_cell(td)
                if len(cand) > len(best):
                    best = cand
                    best_idx = i
            drivers = best
            if driver_idx is None:
                driver_idx = best_idx

        if not drivers:
            continue

        if len(drivers) == 1:
            drivers.append("Unknown")

        car = pick_car_text(tds, header_map, driver_idx)

        row = {
            "year": year,
            "finish": finish,
            "driver1": drivers[0],
            "driver2": drivers[1],
            "car": car,
        }

        # keep one row per finish, preferring:
        # 1) two real names
        # 2) non-empty car
        existing = by_finish.get(finish)
        if existing is None:
            by_finish[finish] = row
        else:
            existing_score = (
                (existing["driver2"] != "Unknown") * 2 +
                (existing["car"] != "") * 1
            )
            new_score = (
                (row["driver2"] != "Unknown") * 2 +
                (row["car"] != "") * 1
            )
            if new_score > existing_score:
                by_finish[finish] = row

    clean_rows = [by_finish[k] for k in sorted(by_finish)]

    print(f"✅ {year}: {len(clean_rows)} rows")
    return clean_rows


def main():
    all_rows = []

    for year in range(START_YEAR, END_YEAR + 1):
        all_rows.extend(parse_year(year))
        time.sleep(1)

    all_rows.sort(key=lambda x: (x["year"], x["finish"]))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["year", "finish", "driver1", "driver2", "car"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"🔥 DONE — {len(all_rows)} rows written to {OUT}")


if __name__ == "__main__":
    main()
