import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (FINAL CLEAN VERSION)")

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if not x:
        return None
    x = re.sub(r"\[[^\]]+\]", "", str(x))
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()


# 🔥 FIXED DRIVER SPLITTING
def split_drivers(text):
    if not text:
        return []

    text = clean(text)

    # normal splits first
    parts = re.split(r"/|,| and | & |\+", text)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) > 1:
        return parts

    # fallback for merged names
    words = text.split()

    drivers = []
    current = []

    for w in words:
        current.append(w)

        # assume names are 2 words (First Last)
        if len(current) == 2:
            drivers.append(" ".join(current))
            current = []

    if current:
        drivers.append(" ".join(current))

    return drivers


def is_driver_text(text):
    if not text:
        return False

    if " " not in text:
        return False

    bad_words = [
        "team", "racing", "motorsport",
        "engineering", "holden", "ford"
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

        if not re.match(r"^\d+$", cols[0] or ""):
            continue

        finish = int(cols[0])

        # 🔥 FIND DRIVER COLUMN PROPERLY
        drivers = []
        driver_index = None

        for i, c in enumerate(cols):
            if is_driver_text(c):
                possible = split_drivers(c)
                if possible:
                    drivers = possible
                    driver_index = i
                    break

        if not drivers:
            continue

        # 🔥 CAR COLUMN (usually next column)
        car = None
        if driver_index is not None and driver_index + 1 < len(cols):
            car = cols[driver_index + 1]

        # 🚨 FINAL CLEAN FILTERS
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

    if not results:
        print(f"⚠️ No clean results {year}")
        return None

    # dedupe
    unique = {}
    for r in results:
        key = (r["finish"], tuple(r["drivers"]))
        unique[key] = r

    final_results = list(unique.values())
    final_results.sort(key=lambda x: x["finish"])

    return {
        "year": year,
        "results": final_results
    }


built = 0

for y in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(y)

    if not data:
        continue

    out = BASE / f"{y}.json"

    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {y} ({len(data['results'])} entries)")
    built += 1

    time.sleep(1)

print(f"🔥 BUILT {built} YEARS")
