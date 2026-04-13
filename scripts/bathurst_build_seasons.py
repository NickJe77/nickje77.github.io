import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (SAFE FIX - CO-DRIVERS ONLY)")

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


# ✅ FIXED DRIVER SPLIT (NO STRUCTURE CHANGE)
def split_drivers(text):
    if not text:
        return []

    text = clean(text)

    parts = re.split(r"/|,| and | & |\+|\n", text)

    drivers = []
    for p in parts:
        p = clean(p)
        if not p:
            continue

        if " " not in p:
            continue

        bad_words = [
            "team", "racing", "motorsport",
            "engineering", "holden", "ford",
            "nissan", "toyota", "audi"
        ]

        if any(b in p.lower() for b in bad_words):
            continue

        drivers.append(p)

    return drivers


def looks_like_driver(text):
    if not text:
        return False

    if " " not in text:
        return False

    bad_words = [
        "team", "racing", "motorsport",
        "engineering", "holden", "ford",
        "nissan", "toyota", "audi"
    ]

    t = text.lower()
    if any(b in t for b in bad_words):
        return False

    return True


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
        cols = [clean(c.get_text(" ", strip=True)) for c in r.find_all("td")]

        if len(cols) < 3:
            continue

        # must be a finishing position
        try:
            finish = int(cols[0])
        except:
            continue

        best_drivers = []
        driver_index = None

        for i, c in enumerate(cols):

            # 🔥 ORIGINAL LOGIC (KEPT)
            d = split_drivers(c)

            # 🔥 ADD THIS (FIX)
            links = []
            for a in r.find_all("a"):
                name = clean(a.get_text(" ", strip=True))
                if looks_like_driver(name):
                    links.append(name)

            # merge both sources
            d = list(dict.fromkeys(d + links))

            if len(d) > len(best_drivers):
                best_drivers = d
                driver_index = i

        drivers = best_drivers

        if not drivers:
            continue

        car = None
        if driver_index is not None and driver_index + 1 < len(cols):
            car = cols[driver_index + 1]

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": car
        })

    if not results:
        print(f"⚠️ No results {year}")
        return None

    # 🔥 IMPROVED DEDUPE (SAFE FIX)
    by_finish = {}
    for r in results:
        f = r["finish"]

        if f not in by_finish:
            by_finish[f] = r
            continue

        existing = by_finish[f]

        existing_drivers = len(existing["drivers"])
        new_drivers = len(r["drivers"])

        # ALWAYS prefer rows with co-drivers
        if existing_drivers < 2 and new_drivers >= 2:
            by_finish[f] = r
            continue

        if new_drivers > existing_drivers:
            by_finish[f] = r

    final_results = list(by_finish.values())
    final_results.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": final_results
    }


# 🚀 BUILD
seasons = []

for year in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(year)

    if not data:
        continue

    results = data["results"]

    winner_drivers = results[0]["drivers"] if results else []
    winner_car = results[0]["car"] if results else None

    # SAVE (UNCHANGED STRUCTURE)
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


# MASTER FILES (UNCHANGED)
seasons.sort(key=lambda x: x["year"])

with open(BASE / "seasons.json", "w", encoding="utf-8") as f:
    json.dump(seasons, f, indent=2, ensure_ascii=False)

with open(BASE / "index.json", "w", encoding="utf-8") as f:
    json.dump({
        "sport": "bathurst",
        "seasons": seasons
    }, f, indent=2, ensure_ascii=False)

print("🔥 DONE")
