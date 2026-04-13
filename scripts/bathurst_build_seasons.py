import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (STABLE FINAL)")

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
        except:
            pass

    return None


# ✅ smarter table detection (not header fragile)
def find_results_table(soup):
    best_table = None
    best_score = 0

    for table in soup.find_all("table", class_="wikitable"):
        text = table.get_text(" ", strip=True).lower()

        score = 0

        # must look like results table
        if "driver" in text:
            score += 2
        if "pos" in text:
            score += 2
        if "laps" in text:
            score += 1
        if "grid" in text:
            score -= 2   # avoid starting grid tables
        if "top 10" in text:
            score -= 3   # avoid shootout

        rows = table.find_all("tr")
        if len(rows) > 10:
            score += 2

        if score > best_score:
            best_score = score
            best_table = table

    return best_table


def looks_like_driver(name):
    if not name:
        return False

    name = clean(name)
    if not name:
        return False

    if re.search(r"\d", name):
        return False

    bad = [
        "team","racing","motorsport","engineering",
        "ford","holden","toyota","nissan","camaro","mustang"
    ]

    if any(b in name.lower() for b in bad):
        return False

    words = name.split()
    return 2 <= len(words) <= 4


def extract_drivers(td):
    drivers = []

    # links first
    for a in td.find_all("a"):
        name = clean(a.get_text())
        if looks_like_driver(name):
            drivers.append(name)

    # fallback split
    if not drivers:
        text = clean(td.get_text(" ", strip=True)) or ""
        parts = re.split(r"/|,| and | & |\+", text)

        for p in parts:
            p = clean(p)
            if looks_like_driver(p):
                drivers.append(p)

    # dedupe
    final = []
    seen = set()

    for d in drivers:
        key = d.lower()
        if key not in seen:
            seen.add(key)
            final.append(d)

    return final[:2]


def fetch_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return None

    print(f"Fetching {year} → {url}")

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    table = find_results_table(soup)

    if not table:
        print(f"❌ No valid table {year}")
        return None

    results = []

    for row in table.find_all("tr"):
        cells = row.find_all("td")

        if len(cells) < 3:
            continue

        cols = [clean(c.get_text(" ", strip=True)) for c in cells]

        try:
            finish = int(cols[0])

            # reject car numbers (888 etc)
            if finish > 60:
                continue

        except:
            continue

        drivers = []
        driver_index = None

        for i, td in enumerate(cells):
            d = extract_drivers(td)
            if len(d) > len(drivers):
                drivers = d
                driver_index = i

        if not drivers:
            continue

        car = None

        for j in range(driver_index + 1, len(cols)):
            c = cols[j]
            if not c:
                continue

            if looks_like_driver(c):
                continue

            car = c
            break

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car
        })

    if not results:
        print(f"⚠️ No results {year}")
        return None

    results.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": results
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
