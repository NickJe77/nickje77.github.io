import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (FINAL – BULLETPROOF)")

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


# 🔥 CORRECT TABLE PICKING
def find_results_table(soup):
    for header in soup.find_all(["h2", "h3"]):
        title = header.get_text().lower()

        if "race results" in title or "classification" in title:

            for table in header.find_all_next("table"):
                if table.find_previous(["h2", "h3"]) != header:
                    break

                text = table.get_text(" ", strip=True).lower()

                if "pos" in text and "driver" in text:
                    return table

    # fallback for old years
    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True).lower()
        if "driver" in text and "pos" in text:
            return table

    return None


def extract_drivers(td):
    names = []

    for a in td.find_all("a"):
        n = clean(a.get_text())
        if n and " " in n:
            names.append(n)

    if not names:
        text = clean(td.get_text(" ", strip=True)) or ""
        parts = re.split(r"/|,| and | & |\+", text)

        for p in parts:
            p = clean(p)
            if p and " " in p:
                names.append(p)

    final = []
    seen = set()

    for n in names:
        k = n.lower()
        if k not in seen:
            seen.add(k)
            final.append(n)

    return final[:2]


# 🔥 INFObox fallback (fixes 2019–2021)
def extract_infobox_winner(soup):
    text = soup.get_text("\n", strip=True)
    lines = [clean(x) for x in text.split("\n")]
    lines = [x for x in lines if x]

    for i, line in enumerate(lines):
        if line == "Winner":

            candidates = []
            for j in range(i + 1, min(i + 8, len(lines))):
                val = lines[j]
                if not val:
                    continue
                if val.lower().startswith("image"):
                    continue
                candidates.append(val)

            names = []
            for val in candidates:
                if len(val.split()) >= 2 and not re.search(r"\d", val):
                    names.append(val)
                if len(names) == 2:
                    break

            team = None
            for val in candidates:
                if val in names:
                    continue
                if not re.search(r"\d", val):
                    team = val
                    break

            if names:
                return {
                    "finish": 1,
                    "drivers": names[:2],
                    "car": team
                }

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

    for row in table.find_all("tr"):

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

        if finish is None:
            continue

        if finish < 1 or finish > 40:
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

    # 🔥 FIX missing winner
    if not any(r["finish"] == 1 for r in results):
        winner = extract_infobox_winner(soup)
        if winner:
            results.append(winner)

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
