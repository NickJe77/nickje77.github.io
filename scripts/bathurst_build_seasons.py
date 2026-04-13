import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (ALL YEARS GUARANTEED)")

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


def looks_like_driver(name):
    if not name:
        return False

    name = clean(name)

    if not name:
        return False

    if re.search(r"\d", name):
        return False

    words = name.split()

    if len(words) < 2 or len(words) > 4:
        return False

    bad = [
        "team","racing","motorsport","engineering",
        "ford","holden","toyota","nissan","camaro","mustang",
        "top","shootout","grid"
    ]

    if any(b in name.lower() for b in bad):
        return False

    return True


def extract_drivers(td):
    names = []

    # linked names
    for a in td.find_all("a"):
        n = clean(a.get_text())
        if looks_like_driver(n):
            names.append(n)

    # fallback split
    if not names:
        text = clean(td.get_text(" ", strip=True)) or ""
        parts = re.split(r"/|,| and | & |\+", text)

        for p in parts:
            p = clean(p)
            if looks_like_driver(p):
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

    results = []

    # 🔥 scan ALL tables
    for table in soup.find_all("table", class_="wikitable"):
        for row in table.find_all("tr"):
            cells = row.find_all("td")

            if len(cells) < 3:
                continue

            cols = [clean(c.get_text(" ", strip=True)) for c in cells]

            # must be real finish number
            try:
                finish = int(cols[0])

                # kill car numbers like 55, 888
                if finish < 1 or finish > 40:
                    continue

            except:
                continue

            # find drivers
            drivers = []
            driver_idx = None

            for i, td in enumerate(cells):
                d = extract_drivers(td)
                if len(d) > len(drivers):
                    drivers = d
                    driver_idx = i

            if not drivers:
                continue

            # find car/team
            car = None
            for j in range(driver_idx + 1, len(cols)):
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

    # 🔥 dedupe by finish
    by_finish = {}
    for r in results:
        f = r["finish"]

        if f not in by_finish:
            by_finish[f] = r
            continue

        # prefer rows with 2 drivers
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
