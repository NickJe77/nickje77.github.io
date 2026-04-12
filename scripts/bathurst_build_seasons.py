import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (CLEAN DATA FIX)")

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if not x:
        return None
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()


def split_drivers(text):
    if not text:
        return []
    parts = re.split(r"/|,| and | & |\+", text)
    return [clean(p) for p in parts if clean(p)]


# 🔥 TRY MULTIPLE PAGE NAMES
def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500",
        f"{year}_Tooheys_1000",
        f"{year}_James_Hardie_1000"
    ]

    for p in patterns:
        url = f"https://en.wikipedia.org/wiki/{p}"
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            return url

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
        cols = [clean(c.get_text()) for c in r.find_all("td")]

        # must have enough columns
        if len(cols) < 3:
            continue

        # ✅ STRICT POSITION CHECK
        if not re.match(r"^\d+$", cols[0] or ""):
            continue

        finish = int(cols[0])

        drivers_raw = cols[2] if len(cols) >= 5 else cols[1]
        car = cols[3] if len(cols) >= 4 else None

        drivers = split_drivers(drivers_raw)

        # 🚨 FILTER GARBAGE
        if not drivers:
            continue

        # too many names = junk row
        if len(drivers) > 4:
            continue

        # absurd long strings = not drivers
        if any(len(d) > 40 for d in drivers):
            continue

        # skip weird rows
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

    with open(out, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved {y} ({len(data['results'])} entries)")
    built += 1

    time.sleep(1)

print(f"🔥 BUILT {built} YEARS")
