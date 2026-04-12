import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (YEARS + SEASONS FILE)")

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


def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500",
        f"{year}_Tooheys_1000",
        f"{year}_James_Hardie_1000",
        f"{year}_AMP_Bathurst_1000",
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


def extract_results(soup):
    results = []

    for r in soup.find_all("tr"):
        cols = [clean(c.get_text(" ", strip=True)) for c in r.find_all("td")]

        if len(cols) < 3:
            continue

        if not re.match(r"^\d+$", cols[0] or ""):
            continue

        finish = int(cols[0])

        drivers_raw = cols[2] if len(cols) >= 5 else cols[1]
        car = cols[3] if len(cols) >= 4 else None

        drivers = split_drivers(drivers_raw)

        if not drivers:
            continue
        if len(drivers) > 4:
            continue
        if any(len(d) > 40 for d in drivers):
            continue
        if any("http" in d.lower() for d in drivers):
            continue

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car
        })

    unique = {}
    for row in results:
        key = (row["finish"], tuple(row["drivers"]), row["car"])
        unique[key] = row

    final_results = list(unique.values())
    final_results.sort(key=lambda x: x["finish"])
    return final_results


def fetch_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return {
            "year": year,
            "race_name": f"{year} Bathurst",
            "results": []
        }

    print(f"Fetching {year} -> {url}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=30)
        if res.status_code != 200:
            print(f"❌ Failed {year}: {res.status_code}")
            return {
                "year": year,
                "race_name": f"{year} Bathurst",
                "results": []
            }
    except Exception as e:
        print(f"❌ Request error {year}: {e}")
        return {
            "year": year,
            "race_name": f"{year} Bathurst",
            "results": []
        }

    soup = BeautifulSoup(res.text, "html.parser")
    results = extract_results(soup)

    race_name = f"{year} Bathurst 1000"
    title = soup.find("title")
    if title:
        title_text = clean(title.get_text())
        if title_text:
            race_name = title_text.replace(" - Wikipedia", "")

    if not results:
        print(f"⚠️ No clean results {year}")

    winner_drivers = results[0]["drivers"] if results else []
    winner_car = results[0]["car"] if results else None

    return {
        "year": year,
        "race_name": race_name,
        "winner_drivers": winner_drivers,
        "winner_car": winner_car,
        "results": results
    }


all_seasons = []
built = 0

for year in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(year)

    # main year file for race page compatibility
    year_file = BASE / f"{year}.json"
    with open(year_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # seasons folder copy
    season_file = SEASONS_DIR / f"{year}.json"
    with open(season_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # summary row for seasons page
    all_seasons.append({
        "year": year,
        "race_name": data.get("race_name"),
        "winner_drivers": data.get("winner_drivers", []),
        "winner_car": data.get("winner_car"),
        "results_count": len(data.get("results", []))
    })

    print(f"✅ Saved {year} ({len(data.get('results', []))} results)")
    built += 1
    time.sleep(1)

all_seasons.sort(key=lambda x: x["year"])

# master seasons file
with open(BASE / "seasons.json", "w", encoding="utf-8") as f:
    json.dump(all_seasons, f, indent=2, ensure_ascii=False)

# index file
with open(BASE / "index.json", "w", encoding="utf-8") as f:
    json.dump({
        "sport": "bathurst",
        "seasons": all_seasons
    }, f, indent=2, ensure_ascii=False)

print(f"🔥 BUILT {built} YEARS")
print("✅ Wrote docs/data/bathurst/seasons.json")
print("✅ Wrote docs/data/bathurst/index.json")
print("✅ Wrote docs/data/bathurst/seasons/{year}.json files")
