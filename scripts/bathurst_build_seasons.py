import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (HARD LOCKED VERSION)")

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


# ✅ ONLY pick results table
def find_results_table(soup):
    for table in soup.find_all("table", class_="wikitable"):
        header_text = table.get_text(" ", strip=True).lower()

        if "driver" in header_text and "laps" in header_text:
            if "grid" in header_text:
                continue
            if "top 10" in header_text:
                continue
            return table

    return None


def get_columns(table):
    header_row = table.find("tr")
    headers = [clean(th.get_text()) for th in header_row.find_all("th")]

    pos = drivers = team = None

    for i, h in enumerate(headers):
        h = h.lower()

        if "pos" in h:
            pos = i
        elif "driver" in h:
            drivers = i
        elif "team" in h or "entrant" in h:
            team = i

    return pos, drivers, team


def extract_drivers(td):
    names = []

    # use links first
    for a in td.find_all("a"):
        name = clean(a.get_text())
        if name and " " in name:
            names.append(name)

    # fallback
    if not names:
        text = clean(td.get_text(" ", strip=True)) or ""
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

    pos_idx, driver_idx, team_idx = get_columns(table)

    results = []

    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")

        if not cells:
            continue

        try:
            finish = int(clean(cells[pos_idx].get_text()))
        except:
            continue

        # this kills car numbers completely
        if finish > 40:
            continue

        drivers = extract_drivers(cells[driver_idx])

        if not drivers:
            continue

        car = None
        if team_idx is not None and team_idx < len(cells):
            car = clean(cells[team_idx].get_text())

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car
        })

    results.sort(key=lambda x: x["finish"])

    if not results:
        print(f"⚠️ No results {year}")
        return None

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
