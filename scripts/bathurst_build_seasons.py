import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (FINAL – STABLE + CO-DRIVER FIXED)")

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


def norm(x):
    return re.sub(r"[^a-z0-9]", "", (x or "").lower())


def split_drivers(text):
    text = clean(text) or ""
    parts = re.split(r"/|,| and | & |\+", text)

    out = []
    seen = set()

    for p in parts:
        p = clean(p)
        if not p or len(p.split()) < 2:
            continue

        k = norm(p)
        if k not in seen:
            seen.add(k)
            out.append(p)

    return out[:2]


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


def find_results_table(soup):
    for header in soup.find_all(["h2", "h3"]):
        title = header.get_text().lower()

        if any(x in title for x in ["race results", "classification", "results"]):
            for table in header.find_all_next("table"):
                if table.find_previous(["h2", "h3"]) != header:
                    break

                text = table.get_text(" ", strip=True).lower()
                if "driver" in text and ("pos" in text or "position" in text):
                    return table

    return None


def fallback_results_table(soup):
    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True).lower()

        if "driver" in text and ("pos" in text or "position" in text):
            return table

    return None


def find_entry_table(soup):
    for header in soup.find_all(["h2", "h3"]):
        title = header.get_text().lower()

        if "entry" in title or "entries" in title or "starting grid" in title:
            table = header.find_next("table")
            if table:
                return table

    return None


def build_driver_map(entry_table):
    mapping = {}

    if not entry_table:
        return mapping

    for row in entry_table.find_all("tr"):
        tds = row.find_all("td")

        if len(tds) < 2:
            continue

        drivers = []
        for td in tds:
            d = split_drivers(td.get_text(" ", strip=True))
            if len(d) >= 2:
                drivers = d
                break

        if len(drivers) == 2:
            mapping[norm(drivers[0])] = drivers
            mapping[norm(drivers[1])] = drivers

    return mapping


def extract_drivers(td):
    names = []

    for a in td.find_all("a"):
        n = clean(a.get_text())
        if n and " " in n:
            names.append(n)

    if not names:
        names = split_drivers(td.get_text(" ", strip=True))

    return names[:2]


def fetch_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return None

    print(f"Fetching {year} → {url}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        print(f"❌ Request failed {year}")
        return None

    results_table = find_results_table(soup)

    # 🔥 FALLBACK
    if not results_table:
        results_table = fallback_results_table(soup)

    # ❌ SKIP IF STILL NONE
    if not results_table:
        print(f"❌ No results table {year}")
        return None

    entry_table = find_entry_table(soup)
    driver_map = build_driver_map(entry_table)

    results = []

    for row in results_table.find_all("tr"):

        ths = row.find_all("th")
        tds = row.find_all("td")

        if not tds:
            continue

        finish = None

        if ths:
            f = clean(ths[0].get_text())
            if f and f.isdigit():
                finish = int(f)

        if finish is None:
            f = clean(tds[0].get_text())
            if f and f.isdigit():
                finish = int(f)

        if finish is None or finish > 60:
            continue

        cols = [clean(td.get_text(" ", strip=True)) for td in tds]

        drivers = []
        driver_idx = None

        for i, td in enumerate(tds):
            d = extract_drivers(td)
            if len(d) > len(drivers):
                drivers = d
                driver_idx = i

        if not drivers:
            continue

        # 🔥 CO-DRIVER FIX
        if len(drivers) == 1:
            key = norm(drivers[0])
            if key in driver_map:
                drivers = driver_map[key]

        car = None
        for j in range(driver_idx + 1, len(cols)):
            c = cols[j]
            if not c:
                continue
            if c in drivers:
                continue
            car = c
            break

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car
        })

    if not results:
        print(f"⚠️ No parsed rows {year}")
        return None

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
