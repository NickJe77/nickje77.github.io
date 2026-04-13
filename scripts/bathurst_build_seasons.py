import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (RESULTS + ENTRANTS FIX)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"

BASE.mkdir(parents=True, exist_ok=True)
SEASONS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if x is None:
        return None
    x = re.sub(r"\[[^\]]+\]", "", str(x))
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x or None


def normalize_key(x):
    x = clean(x) or ""
    return re.sub(r"[^a-z0-9]+", "", x.lower())


def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500",
        f"{year}_Tooheys_1000",
        f"{year}_James_Hardie_1000",
        f"{year}_AMP_Bathurst_1000"
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


def looks_like_driver(name):
    name = clean(name)
    if not name:
        return False

    lower = name.lower()

    # reject obvious junk
    banned_terms = [
        "team", "racing", "motorsport", "engineering",
        "ford", "holden", "toyota", "nissan", "chevrolet",
        "camaro", "mustang", "commodore", "falcon",
        "top 10", "shootout", "grid", "pole", "laps",
        "time", "class", "race", "results", "position",
        "car", "number", "no.", "entrant", "driver(s)"
    ]
    if any(term in lower for term in banned_terms):
        return False

    # allow apostrophes and particles like de
    if re.search(r"\d", name):
        return False

    words = name.split()
    if len(words) < 2 or len(words) > 4:
        return False

    return True


def extract_drivers_from_cell(td):
    drivers = []

    # Linked names first
    for a in td.find_all("a"):
        txt = clean(a.get_text(" ", strip=True))
        if looks_like_driver(txt):
            drivers.append(txt)

    # Fallback text split
    if not drivers:
        raw = clean(td.get_text(" ", strip=True)) or ""
        parts = re.split(r"/|,| and | & |\+|\n", raw)
        for part in parts:
            part = clean(part)
            if looks_like_driver(part):
                drivers.append(part)

    # de-dupe preserving order
    final = []
    seen = set()
    for d in drivers:
        k = normalize_key(d)
        if k and k not in seen:
            seen.add(k)
            final.append(d)

    return final


def table_header_cells(table):
    rows = table.find_all("tr")
    for tr in rows[:3]:
        ths = tr.find_all("th")
        if ths:
            return [clean(th.get_text(" ", strip=True)) or "" for th in ths]
    return []


def classify_header(text):
    t = (text or "").lower()

    if t in {"pos", "position", "place", "fin", "finish"}:
        return "finish"

    if "pos" in t or "position" in t or "finish" in t:
        return "finish"

    if t in {"no", "number", "car no", "car", "no."}:
        return "car_no"

    if "car no" in t or "number" in t or t == "no" or t == "no.":
        return "car_no"

    if "driver" in t:
        return "drivers"

    if "team" in t or "entrant" in t:
        return "team"

    if "vehicle" in t or "model" in t or "car" in t:
        return "vehicle"

    return None


def find_best_results_table(soup):
    best = None
    best_score = -999

    for table in soup.find_all("table", class_="wikitable"):
        headers = table_header_cells(table)
        if not headers:
            continue

        classes = [classify_header(h) for h in headers]
        text = " | ".join(h.lower() for h in headers)

        score = 0

        if "finish" in classes:
            score += 8
        if "drivers" in classes:
            score += 8
        if "team" in classes or "vehicle" in classes:
            score += 3

        # avoid entry/starting-grid tables
        if "grid" in text:
            score -= 8
        if "starting grid" in text:
            score -= 10
        if "shootout" in text or "top 10" in text:
            score -= 10
        if "entry list" in text or "entries" in text:
            score -= 8

        row_count = len(table.find_all("tr"))
        if row_count >= 10:
            score += 2

        if score > best_score:
            best_score = score
            best = table

    return best


def find_best_entrants_table(soup):
    best = None
    best_score = -999

    for table in soup.find_all("table", class_="wikitable"):
        headers = table_header_cells(table)
        if not headers:
            continue

        classes = [classify_header(h) for h in headers]
        text = " | ".join(h.lower() for h in headers)

        score = 0

        if "car_no" in classes:
            score += 8
        if "drivers" in classes:
            score += 8
        if "team" in classes or "vehicle" in classes:
            score += 3

        if "grid" in text or "starting grid" in text or "entry" in text or "entries" in text:
            score += 4

        if "finish" in classes:
            score -= 6

        if score > best_score:
            best_score = score
            best = table

    return best


def map_columns(headers):
    mapping = {}
    for i, h in enumerate(headers):
        c = classify_header(h)
        if c and c not in mapping:
            mapping[c] = i
    return mapping


def extract_table_rows(table):
    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if tr.find_all("td"):
            rows.append(tr)
    return rows


def parse_entrants_map(table):
    entrants_by_car_no = {}
    entrants_by_team = {}
    entrants_by_driver = {}

    if not table:
        return entrants_by_car_no, entrants_by_team, entrants_by_driver

    headers = table_header_cells(table)
    colmap = map_columns(headers)
    rows = extract_table_rows(table)

    car_no_idx = colmap.get("car_no")
    drivers_idx = colmap.get("drivers")
    team_idx = colmap.get("team")

    if drivers_idx is None:
        return entrants_by_car_no, entrants_by_team, entrants_by_driver

    for tr in rows:
        tds = tr.find_all("td")
        if not tds:
            continue

        # Some tables have fewer cells because of rowspans; ignore those rows
        max_needed = max([i for i in [car_no_idx, drivers_idx, team_idx] if i is not None], default=0)
        if len(tds) <= max_needed:
            continue

        drivers = extract_drivers_from_cell(tds[drivers_idx])
        if not drivers:
            continue

        team = clean(tds[team_idx].get_text(" ", strip=True)) if team_idx is not None and team_idx < len(tds) else None
        car_no = clean(tds[car_no_idx].get_text(" ", strip=True)) if car_no_idx is not None and car_no_idx < len(tds) else None

        entry = {
            "drivers": drivers[:2],
            "team": team,
            "car_no": car_no
        }

        if car_no:
            entrants_by_car_no[normalize_key(car_no)] = entry
        if team:
            entrants_by_team[normalize_key(team)] = entry

        for d in drivers:
            entrants_by_driver[normalize_key(d)] = entry

    return entrants_by_car_no, entrants_by_team, entrants_by_driver


def parse_results_table(table, entrants_by_car_no, entrants_by_team, entrants_by_driver):
    if not table:
        return []

    headers = table_header_cells(table)
    colmap = map_columns(headers)
    rows = extract_table_rows(table)

    finish_idx = colmap.get("finish")
    drivers_idx = colmap.get("drivers")
    team_idx = colmap.get("team")
    car_no_idx = colmap.get("car_no")
    vehicle_idx = colmap.get("vehicle")

    results = []

    for tr in rows:
        tds = tr.find_all("td")
        if not tds:
            continue

        max_needed = max([i for i in [finish_idx, drivers_idx, team_idx, car_no_idx, vehicle_idx] if i is not None], default=0)
        if len(tds) <= max_needed:
            continue

        if finish_idx is None or finish_idx >= len(tds):
            continue

        finish_text = clean(tds[finish_idx].get_text(" ", strip=True))
        if not finish_text:
            continue

        # only classified finish numbers, not car numbers
        if not re.fullmatch(r"\d{1,2}", finish_text):
            continue

        finish = int(finish_text)
        if finish < 1 or finish > 40:
            continue

        drivers = []
        if drivers_idx is not None and drivers_idx < len(tds):
            drivers = extract_drivers_from_cell(tds[drivers_idx])

        team = clean(tds[team_idx].get_text(" ", strip=True)) if team_idx is not None and team_idx < len(tds) else None
        car_no = clean(tds[car_no_idx].get_text(" ", strip=True)) if car_no_idx is not None and car_no_idx < len(tds) else None

        # prefer entrant/team in car column for your page
        car = None
        if team:
            car = team
        elif vehicle_idx is not None and vehicle_idx < len(tds):
            car = clean(tds[vehicle_idx].get_text(" ", strip=True))

        # backfill missing co-driver from entrant map
        if len(drivers) < 2:
            entry = None

            if car_no and normalize_key(car_no) in entrants_by_car_no:
                entry = entrants_by_car_no[normalize_key(car_no)]
            elif team and normalize_key(team) in entrants_by_team:
                entry = entrants_by_team[normalize_key(team)]
            elif drivers:
                first_key = normalize_key(drivers[0])
                if first_key in entrants_by_driver:
                    entry = entrants_by_driver[first_key]

            if entry and entry.get("drivers"):
                enriched = []
                seen = set()

                for d in drivers + entry["drivers"]:
                    k = normalize_key(d)
                    if k and k not in seen:
                        seen.add(k)
                        enriched.append(d)

                drivers = enriched[:2]

        if not drivers:
            continue

        results.append({
            "finish": finish,
            "drivers": drivers[:2],
            "car": car
        })

    # dedupe by finish
    by_finish = {}
    for row in results:
        f = row["finish"]
        if f not in by_finish:
            by_finish[f] = row
            continue

        existing = by_finish[f]

        if len(row.get("drivers", [])) > len(existing.get("drivers", [])):
            by_finish[f] = row
            continue

        if not existing.get("car") and row.get("car"):
            by_finish[f] = row

    final = list(by_finish.values())
    final.sort(key=lambda x: x["finish"])
    return final


def fetch_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return None

    print(f"Fetching {year} → {url}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=30)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Request failed for {year}: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    results_table = find_best_results_table(soup)
    entrants_table = find_best_entrants_table(soup)

    entrants_by_car_no, entrants_by_team, entrants_by_driver = parse_entrants_map(entrants_table)
    results = parse_results_table(results_table, entrants_by_car_no, entrants_by_team, entrants_by_driver)

    if not results:
        print(f"⚠️ No results {year}")
        return None

    return {
        "year": year,
        "results": results
    }


seasons = []

for year in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(year)

    if not data:
        continue

    results = data["results"]

    winner_drivers = results[0]["drivers"] if results else []
    winner_car = results[0]["car"] if results else None

    with open(BASE / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with open(SEASONS_DIR / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    seasons.append({
        "year": year,
        "winner_drivers": winner_drivers,
        "winner_car": winner_car
    })

    print(f"✅ Saved {year} ({len(results)} rows)")
    time.sleep(1)

seasons.sort(key=lambda x: x["year"])

with open(BASE / "seasons.json", "w", encoding="utf-8") as f:
    json.dump(seasons, f, indent=2, ensure_ascii=False)

with open(BASE / "index.json", "w", encoding="utf-8") as f:
    json.dump({
        "sport": "bathurst",
        "seasons": seasons
    }, f, indent=2, ensure_ascii=False)

print("🔥 DONE")
