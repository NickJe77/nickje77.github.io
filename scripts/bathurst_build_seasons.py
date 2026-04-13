import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (TABLE LOCKED - FINAL)")

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

    # linked names
    for a in td.find_all("a"):
        name = clean(a.get_text())
        if looks_like_driver(name):
            drivers.append(name)

    # fallback split
    text = clean(td.get_text(" ", strip=True)) or ""
    parts = re.split(r"/|,| and | & |\+|\n", text)

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


def find_results_table(soup):
    # ONLY pick table with "Classified" or "Results"
    for header in soup.find_all(["h2", "h3"]):
        title = header.get_text().lower()

        if "classification" in title or "results" in title:
            table = header.find_next("table", class_="wikitable")
            if table:
                return table

    return None


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

    for r in table.find_all("tr"):
        tds = r.find_all("td")

        if len(tds) < 4:
            continue

        cols = [clean(td.get_text(" ", strip=True)) for td in tds]

        # finish MUST be small number (not car number)
        try:
            finish = int(cols[0])
            if finish > 60:  # avoids car numbers like 888, 100, etc
                continue
        except:
            continue

        # drivers usually in column 2 or 3
        drivers = []
        for td in tds:
            d = extract_drivers(td)
            if len(d) >= 1:
                drivers = d
                break

        if not drivers:
            continue

        drivers = drivers[:2]

        # car/team = last column usually
        car = cols[-1]

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
