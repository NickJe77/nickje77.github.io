import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (CLEAN DRIVERS FINAL)")

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
    return re.sub(r"\s+", " ", x).strip()


def looks_like_driver(name):
    if not name:
        return False

    name = clean(name)
    if not name:
        return False

    # remove numbers / junk
    if re.search(r"\d", name):
        return False

    bad = [
        "team","racing","motorsport","engineering",
        "top","shootout","grid","lap","km",
        "ford","holden","toyota","nissan","camaro","mustang"
    ]
    if any(b in name.lower() for b in bad):
        return False

    words = name.split()

    # allow 2–3 word names (Anton de Pasquale etc)
    return 2 <= len(words) <= 3


def extract_drivers(td):
    drivers = []

    # 1. linked names (most reliable)
    for a in td.find_all("a"):
        name = clean(a.get_text())
        if looks_like_driver(name):
            drivers.append(name)

    # 2. fallback split
    text = clean(td.get_text(" ", strip=True)) or ""
    parts = re.split(r"/|,| and | & |\+|\n", text)

    for p in parts:
        p = clean(p)
        if looks_like_driver(p):
            drivers.append(p)

    # 🔥 CLEAN + REMOVE COMBINED STRINGS
    final = []
    seen = set()

    for d in drivers:
        key = d.lower()

        # remove long combined junk like "Will Brown Scott Pye"
        if len(d.split()) > 3:
            continue

        if key not in seen:
            seen.add(key)
            final.append(d)

    return final


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
        except:
            pass

    return None


def fetch_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return None

    print(f"Fetching {year} → {url}")

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    results = []

    for r in soup.find_all("tr"):
        tds = r.find_all("td")

        if len(tds) < 3:
            continue

        cols = [clean(td.get_text(" ", strip=True)) for td in tds]

        try:
            finish = int(cols[0])
        except:
            continue

        best_drivers = []
        driver_index = None

        for i, td in enumerate(tds):
            d = extract_drivers(td)

            if len(d) > len(best_drivers):
                best_drivers = d
                driver_index = i

        if not best_drivers:
            continue

        # keep ONLY first 2 drivers (Bathurst rule)
        drivers = best_drivers[:2]

        # 🔥 FIX CAR COLUMN
        car = None
        for j in range(driver_index + 1, len(cols)):
            candidate = cols[j]
            if not candidate:
                continue

            # reject if looks like driver text
            if looks_like_driver(candidate):
                continue

            # reject if same as drivers joined
            if candidate.lower() == " ".join(drivers).lower():
                continue

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

    # dedupe by finish
    by_finish = {}
    for r in results:
        f = r["finish"]

        if f not in by_finish:
            by_finish[f] = r
            continue

        if len(r["drivers"]) > len(by_finish[f]["drivers"]):
            by_finish[f] = r

    final_results = list(by_finish.values())
    final_results.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": final_results
    }


# BUILD
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
