import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (FULL FIELD + CO-DRIVER SAFER)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

BASE.mkdir(parents=True, exist_ok=True)
SEASONS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if x is None:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]*\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x or None


def looks_like_person(name):
    if not name:
        return False

    n = clean(name)
    if not n:
        return False

    bad_terms = [
        "team", "racing", "motorsport", "engineering", "performance",
        "holden", "ford", "nissan", "toyota", "mazda", "audi", "bmw",
        "mercedes", "porsche", "volkswagen", "renault", "volvo", "honda",
        "datsun", "peugeot", "mini", "chevrolet", "chrysler", "ferrari",
        "dealer", "motors", "cars", "car", "garage", "works", "factory"
    ]

    lower = n.lower()
    if any(term in lower for term in bad_terms):
        return False

    if len(n.split()) < 2:
        return False

    if re.search(r"\d", n):
        return False

    return True


def is_position_value(text):
    if not text:
        return False
    t = clean(text)
    if not t:
        return False
    return bool(re.fullmatch(r"\d+", t))


def get_candidate_urls(year):
    return [
        f"https://en.wikipedia.org/wiki/{year}_Bathurst_1000",
        f"https://en.wikipedia.org/wiki/{year}_Bathurst_500",
        f"https://en.wikipedia.org/wiki/{year}_Hardie-Ferodo_1000",
        f"https://en.wikipedia.org/wiki/{year}_Hardie-Ferodo_500",
        f"https://en.wikipedia.org/wiki/{year}_Tooheys_1000",
        f"https://en.wikipedia.org/wiki/{year}_James_Hardie_1000",
        f"https://en.wikipedia.org/wiki/{year}_AMP_Bathurst_1000",
    ]


def get_url(year):
    for url in get_candidate_urls(year):
        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            if res.status_code == 200 and "Wikipedia does not have an article with this exact name" not in res.text:
                return url
        except Exception:
            pass
    return None


def extract_people_from_cell(td):
    drivers = []

    # Prefer linked names first
    for a in td.find_all("a"):
        txt = clean(a.get_text(" ", strip=True))
        if looks_like_person(txt):
            drivers.append(txt)

    # If no linked names, fall back to raw text splitting
    if not drivers:
        raw = clean(td.get_text(" ", strip=True)) or ""
        parts = re.split(r"/|,| and | & |\+|\n", raw)
        for part in parts:
            part = clean(part)
            if looks_like_person(part):
                drivers.append(part)

    # Deduplicate while preserving order
    out = []
    seen = set()
    for d in drivers:
        key = d.lower()
        if key not in seen:
            seen.add(key)
            out.append(d)

    return out


def normalize_car(text):
    t = clean(text)
    if not t:
        return None
    return t


def score_result_row(row):
    """
    Give each row a score so we can prefer proper result rows.
    """
    score = 0
    finish = row.get("finish")
    drivers = row.get("drivers") or []
    car = row.get("car")

    if isinstance(finish, int):
        score += 5

    if drivers:
        score += 10
        score += min(len(drivers), 3) * 4

    if car:
        score += 3

    return score


def parse_result_table(table):
    rows = []

    tr_list = table.find_all("tr")
    for tr in tr_list:
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        texts = [clean(td.get_text(" ", strip=True)) for td in tds]
        texts = [t for t in texts if t]

        if not texts:
            continue

        # first numeric cell is the best candidate for finish
        finish = None
        finish_idx = None
        for i, txt in enumerate(texts[:3]):
            if is_position_value(txt):
                finish = int(txt)
                finish_idx = i
                break

        if finish is None:
            continue

        # Re-grab original TDs, matching by position in row
        # Use actual cells for better extraction
        best_driver_list = []
        best_driver_idx = None

        for i, td in enumerate(tds):
            cell_drivers = extract_people_from_cell(td)
            if len(cell_drivers) > len(best_driver_list):
                best_driver_list = cell_drivers
                best_driver_idx = i

        if not best_driver_list:
            continue

        car = None
        if best_driver_idx is not None:
            # Usually car is next non-empty cell after driver cell
            for j in range(best_driver_idx + 1, len(tds)):
                candidate = normalize_car(tds[j].get_text(" ", strip=True))
                if not candidate:
                    continue

                if candidate in best_driver_list:
                    continue

                if looks_like_person(candidate):
                    continue

                car = candidate
                break

        row = {
            "finish": finish,
            "drivers": best_driver_list,
            "car": car
        }
        row["_score"] = score_result_row(row)
        rows.append(row)

    return rows


def choose_best_table(soup):
    best_rows = []
    best_score = -1

    for table in soup.find_all("table", class_="wikitable"):
        parsed = parse_result_table(table)
        if not parsed:
            continue

        table_score = sum(r["_score"] for r in parsed)

        # Bonus if table looks like a proper field/classification table
        header_text = clean(table.get_text(" ", strip=True)) or ""
        header_lower = header_text.lower()

        if "driver" in header_lower or "drivers" in header_lower:
            table_score += 20
        if "car" in header_lower:
            table_score += 10
        if "class" in header_lower:
            table_score += 5
        if "laps" in header_lower:
            table_score += 5
        if "grid" in header_lower:
            table_score -= 10

        if len(parsed) > len(best_rows):
            table_score += 10

        if table_score > best_score:
            best_score = table_score
            best_rows = parsed

    return best_rows


def dedupe_rows_keep_best(rows):
    by_finish = {}

    for row in rows:
        finish = row["finish"]
        if finish not in by_finish:
            by_finish[finish] = row
            continue

        existing = by_finish[finish]

        # prefer more drivers, then better score, then longer car text
        existing_drivers = len(existing.get("drivers") or [])
        new_drivers = len(row.get("drivers") or [])

        if new_drivers > existing_drivers:
            by_finish[finish] = row
            continue

        if new_drivers == existing_drivers:
            if row.get("_score", 0) > existing.get("_score", 0):
                by_finish[finish] = row
                continue

            existing_car_len = len(existing.get("car") or "")
            new_car_len = len(row.get("car") or "")
            if new_car_len > existing_car_len:
                by_finish[finish] = row

    final_rows = []
    for finish in sorted(by_finish):
        row = dict(by_finish[finish])
        row.pop("_score", None)
        final_rows.append(row)

    return final_rows


def fetch_year(year):
    url = get_url(year)
    if not url:
        print(f"❌ No page for {year}")
        return None

    print(f"Fetching {year} -> {url}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=30)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Request failed for {year}: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    parsed_rows = choose_best_table(soup)
    parsed_rows = dedupe_rows_keep_best(parsed_rows)

    if not parsed_rows:
        print(f"⚠️ No result rows found for {year}")
        return None

    winner_drivers = parsed_rows[0]["drivers"] if parsed_rows else []
    winner_car = parsed_rows[0]["car"] if parsed_rows else None

    data = {
        "year": year,
        "race": "Bathurst 1000",
        "source": url,
        "winner_drivers": winner_drivers,
        "winner_car": winner_car,
        "results": parsed_rows
    }

    return data


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build():
    seasons_index = []

    for year in range(START_YEAR, END_YEAR + 1):
        data = fetch_year(year)
        if not data:
            continue

        save_json(SEASONS_DIR / f"{year}.json", data)

        seasons_index.append({
            "year": year,
            "winner_drivers": data.get("winner_drivers", []),
            "winner_car": data.get("winner_car")
        })

        print(f"✅ Saved {year} ({len(data['results'])} rows)")
        time.sleep(1)

    seasons_index.sort(key=lambda x: x["year"])

    save_json(
        BASE / "seasons.json",
        seasons_index
    )

    save_json(
        INDEX_FILE,
        {
            "sport": "bathurst",
            "seasons": seasons_index
        }
    )

    print("🔥 DONE")


if __name__ == "__main__":
    build()
