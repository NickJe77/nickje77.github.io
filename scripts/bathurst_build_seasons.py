import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (FINAL SAFER FIELD FIX)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"

BASE.mkdir(parents=True, exist_ok=True)
SEASONS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if not x:
        return None
    x = re.sub(r"\[[^\]]+\]", "", str(x))
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x or None


def has_bad_term(text):
    t = (text or "").lower()
    bad_words = [
        "team", "racing", "motorsport", "engineering",
        "shootout", "top 10", "top ten", "pole", "grid",
        "laps", "km", "practice", "qualifying", "driver(s)",
        "position", "car", "class", "time", "notes"
    ]
    return any(b in t for b in bad_words)


def looks_like_driver(text):
    if not text:
        return False

    text = clean(text)
    if not text:
        return False

    # kill junk like Top 10
    if re.search(r"\d", text):
        return False

    if has_bad_term(text):
        return False

    words = text.split()

    # allow Anton de Pasquale etc
    if len(words) < 2 or len(words) > 4:
        return False

    # must mostly look like name words
    for w in words:
        if len(w) == 1:
            return False

    lower = text.lower()

    # obvious non-driver manufacturer / car strings
    banned = [
        "camaro", "mustang", "commodore", "falcon", "nissan",
        "holden", "ford", "toyota", "audi", "bmw", "mercedes",
        "porsche", "mazda", "volvo", "chevrolet"
    ]
    if any(b in lower for b in banned):
        return False

    return True


def split_drivers(text):
    if not text:
        return []

    text = clean(text)
    if not text:
        return []

    parts = re.split(r"/|,| and | & |\+|\n", text)

    out = []
    seen = set()

    for p in parts:
        p = clean(p)
        if not p:
            continue
        if looks_like_driver(p):
            key = p.lower()
            if key not in seen:
                seen.add(key)
                out.append(p)

    return out


def clean_driver_list(drivers):
    final = []
    seen = set()

    for d in drivers:
        d = clean(d)
        if not d:
            continue
        if not looks_like_driver(d):
            continue

        key = d.lower()
        if key not in seen:
            seen.add(key)
            final.append(d)

    return final


def extract_links_from_cell(td):
    names = []
    seen = set()

    for a in td.find_all("a"):
        name = clean(a.get_text(" ", strip=True))
        if looks_like_driver(name):
            key = name.lower()
            if key not in seen:
                seen.add(key)
                names.append(name)

    return names


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
            res = requests.get(url, headers=HEADERS, timeout=20)
            if res.status_code == 200:
                return url
        except Exception:
            pass

    return None


def looks_like_car_or_team(text, drivers):
    text = clean(text)
    if not text:
        return False

    lower = text.lower()

    # reject obvious junk
    if re.search(r"^\d+$", text):
        return False

    if lower in {"ret", "dnf", "dns", "dsq", "nc"}:
        return False

    # if this cell is basically just the drivers again, reject
    joined_drivers = " ".join(drivers).lower().strip()
    if joined_drivers and lower == joined_drivers:
        return False

    # reject if it's just names
    if looks_like_driver(text):
        return False

    # accept common team/car patterns
    good_terms = [
        "racing", "motorsport", "engineering", "team", "united",
        "grove", "premiair", "erebus", "tickford", "blanchard",
        "brad jones", "triple eight", "walkinshaw", "dick johnson",
        "team 18", "matt stone", "camaro", "mustang", "commodore",
        "falcon", "chevrolet", "ford", "holden", "nissan", "toyota"
    ]
    if any(term in lower for term in good_terms):
        return True

    # fallback: multi-word non-driver text can still be a team/car
    return len(text.split()) >= 2


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
    results = []

    for r in soup.find_all("tr"):
        tds = r.find_all("td")
        if len(tds) < 3:
            continue

        cols = [clean(td.get_text(" ", strip=True)) for td in tds]

        try:
            finish = int(cols[0])
        except Exception:
            continue

        best_drivers = []
        driver_index = None

        for i, td in enumerate(tds):
            cell_text = clean(td.get_text(" ", strip=True)) or ""
            text_drivers = split_drivers(cell_text)
            link_drivers = extract_links_from_cell(td)

            cell_drivers = clean_driver_list(text_drivers + link_drivers)

            if len(cell_drivers) > len(best_drivers):
                best_drivers = cell_drivers
                driver_index = i

        drivers = clean_driver_list(best_drivers)

        if not drivers:
            continue

        car = None

        # Prefer next sensible non-driver cell after the driver cell
        if driver_index is not None:
            for j in range(driver_index + 1, len(cols)):
                candidate = cols[j]
                if looks_like_car_or_team(candidate, drivers):
                    car = candidate
                    break

        # fallback: scan all cells except finish and driver cell
        if not car:
            for j, candidate in enumerate(cols):
                if j == 0 or j == driver_index:
                    continue
                if looks_like_car_or_team(candidate, drivers):
                    car = candidate
                    break

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car
        })

    if not results:
        print(f"⚠️ No results {year}")
        return None

    by_finish = {}
    for row in results:
        finish = row["finish"]

        if finish not in by_finish:
            by_finish[finish] = row
            continue

        existing = by_finish[finish]

        existing_drivers = len(existing.get("drivers", []))
        new_drivers = len(row.get("drivers", []))

        # prefer two-driver rows over one-driver rows
        if existing_drivers < 2 and new_drivers >= 2:
            by_finish[finish] = row
            continue

        if new_drivers > existing_drivers:
            by_finish[finish] = row
            continue

        # if driver count equal, prefer row that has a car/team
        if not existing.get("car") and row.get("car"):
            by_finish[finish] = row

    final_results = list(by_finish.values())
    final_results.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": final_results
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
