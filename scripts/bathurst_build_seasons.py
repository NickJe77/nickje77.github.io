import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (FULL SYSTEM FIXED)")

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


def split_drivers(text):
    if not text:
        return []
    parts = re.split(r"/|,| and | & |\+", text)
    return [clean(p) for p in parts if clean(p)]


# 🔥 FIND CORRECT PAGE
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


# 🔥 FIND RESULTS TABLE + COLUMN INDEXES
def find_table(soup):
    tables = soup.find_all("table", {"class": "wikitable"})

    for table in tables:
        headers = [clean(th.get_text()) for th in table.find_all("th")]

        if not headers:
            continue

        if any("pos" in h.lower() for h in headers) and \
           any("driver" in h.lower() for h in headers):

            return table, headers

    return None, None


def fetch_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return None

    print(f"Fetching {year} → {url}")

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    table, headers = find_table(soup)

    if not table:
        print(f"⚠️ No table {year}")
        return None

    # 🔥 GET COLUMN INDEXES
    driver_idx = None
    car_idx = None

    for i, h in enumerate(headers):
        h = h.lower()
        if "driver" in h:
            driver_idx = i
        if "car" in h or "vehicle" in h:
            car_idx = i

    if driver_idx is None:
        print(f"⚠️ No driver column {year}")
        return None

    results = []

    for r in table.find_all("tr"):
        cols = [clean(c.get_text(" ", strip=True)) for c in r.find_all("td")]

        if len(cols) <= driver_idx:
            continue

        try:
            finish = int(cols[0])
        except:
            continue

        drivers = split_drivers(cols[driver_idx])
        car = cols[car_idx] if car_idx is not None and car_idx < len(cols) else None

        if not drivers:
            continue

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car
        })

    # 🔥 REMOVE DUPLICATES (KEEP FULL DRIVER ROW)
    by_finish = {}
    for r in results:
        f = r["finish"]
        if f not in by_finish or len(r["drivers"]) > len(by_finish[f]["drivers"]):
            by_finish[f] = r

    final_results = list(by_finish.values())
    final_results.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": final_results
    }


# ========================
# 🚀 BUILD EVERYTHING
# ========================

seasons = []
built = 0

for year in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(year)

    if not data:
        continue

    results = data["results"]

    # 🔥 WINNER (CORRECT)
    winner_drivers = results[0]["drivers"] if results else []
    winner_car = results[0]["car"] if results else None

    # YEAR FILE
    with open(BASE / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # SEASON FILE COPY
    with open(SEASONS_DIR / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # SEASONS SUMMARY
    seasons.append({
        "year": year,
        "winner_drivers": winner_drivers,
        "winner_car": winner_car
    })

    print(f"✅ Saved {year} ({len(results)} results)")
    built += 1

    time.sleep(1)


# 🔥 WRITE MASTER FILES

seasons.sort(key=lambda x: x["year"])

with open(BASE / "seasons.json", "w", encoding="utf-8") as f:
    json.dump(seasons, f, indent=2, ensure_ascii=False)

with open(BASE / "index.json", "w", encoding="utf-8") as f:
    json.dump({
        "sport": "bathurst",
        "seasons": seasons
    }, f, indent=2, ensure_ascii=False)

print(f"🔥 BUILT {built} YEARS")
print("✅ seasons.json + index.json written")
