import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (CLEAN RESET VERSION)")

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
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x or None


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


# ✅ FIND CORRECT RESULTS TABLE
def find_results_table(soup):
    best = None
    best_rows = 0

    for table in soup.find_all("table", class_="wikitable"):
        text = table.get_text(" ", strip=True).lower()

        # must look like results
        if "driver" not in text or "pos" not in text:
            continue

        # exclude bad tables
        if "grid" in text or "shootout" in text or "entry" in text:
            continue

        rows = len(table.find_all("tr"))

        if rows > best_rows:
            best_rows = rows
            best = table

    return best


def extract_drivers(cell):
    names = []

    # linked names
    for a in cell.find_all("a"):
        name = clean(a.get_text())
        if name and " " in name:
            names.append(name)

    # fallback
    if not names:
        text = clean(cell.get_text(" ", strip=True)) or ""
        parts = re.split(r"/|,| and | & |\+", text)

        for p in parts:
            p = clean(p)
            if p and " " in p:
                names.append(p)

    # dedupe
    final = []
    seen = set()

    for n in names:
        k = n.lower()
        if k not in seen:
            seen.add(k)
            final.append(n)

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
        print(f"❌ No results table {year}")
        return None

    results = []

    for row in table.find_all("tr"):
        cells = row.find_all("td")

        if len(cells) < 3:
            continue

        # finish position
        try:
            finish = int(clean(cells[0].get_text()))
        except:
            continue

        # ignore car numbers pretending to be positions
        if finish > 40:
            continue

        # drivers = longest cell with names
        drivers = []
        driver_idx = None

        for i, td in enumerate(cells):
            d = extract_drivers(td)
            if len(d) > len(drivers):
                drivers = d
                driver_idx = i

        if not drivers:
            continue

        # car/team = next non-driver cell
        car = None
        for j in range(driver_idx + 1, len(cells)):
            txt = clean(cells[j].get_text())

            if not txt:
                continue

            if txt in drivers:
                continue

            car = txt
            break

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car
        })

    if not results:
        print(f"⚠️ No results {year}")
        return None

    # dedupe
    by_finish = {}
    for r in results:
        f = r["finish"]

        if f not in by_finish:
            by_finish[f] = r
            continue

        if len(r["drivers"]) > len(by_finish[f]["drivers"]):
            by_finish[f] = r

    final = list(by_finish.values())
    final.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": final
    }


# BUILD
seasons = []

for year in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(year)

    if not data:
        continue

    results = data["results"]

    winner_drivers = results[0]["drivers"]
    winner_car = results[0]["car"]

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
