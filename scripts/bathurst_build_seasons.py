import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (DRIVERS FIXED)")

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


def split_drivers(text):
    if not text:
        return []
    parts = re.split(r"/|,| and | & |\+", text)
    return [clean(p) for p in parts if clean(p)]


def is_driver_text(text):
    if not text:
        return False

    # must contain at least one space (first + last name)
    if " " not in text:
        return False

    # reject obvious team words
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
        cols = [clean(c.get_text(" ", strip=True)) for c in r.find_all("td")]

        if len(cols) < 3:
            continue

        if not re.match(r"^\d+$", cols[0] or ""):
            continue

        finish = int(cols[0])

        # 🔥 FIND DRIVER COLUMN DYNAMICALLY
        drivers = []
        for c in cols:
            if is_driver_text(c):
                drivers = split_drivers(c)
                if drivers:
                    break

        if not drivers:
            continue

        # car is usually next column after drivers
        car = None
        for i, c in enumerate(cols):
            if c in drivers:
                if i + 1 < len(cols):
                    car = cols[i + 1]
                break

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


for y in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(y)

    if not data:
        continue

    out = BASE / f"{y}.json"

    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {y} ({len(data['results'])} entries)")

    time.sleep(1)

print("🔥 DONE")
