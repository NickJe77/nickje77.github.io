import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST BUILDER (STRUCTURED TABLE FIX)")

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
    tables = soup.find_all("table", {"class": "wikitable"})

    for table in tables:
        headers = [clean(th.get_text()) for th in table.find_all("th")]

        if not headers:
            continue

        header_text = " ".join(headers).lower()

        if "driver" in header_text or "drivers" in header_text:
            if "position" in header_text or "pos" in header_text:
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
        print(f"⚠️ No results table {year}")
        return None

    results = []

    for r in table.find_all("tr"):
        cols = [clean(c.get_text(" ", strip=True)) for c in r.find_all("td")]

        if len(cols) < 3:
            continue

        try:
            finish = int(cols[0])
        except:
            continue

        # 🔥 find drivers column properly
        drivers = []
        for c in cols:
            if c and len(c.split()) >= 2:
                possible = split_drivers(c)
                if possible and len(possible) <= 4:
                    drivers = possible
                    break

        if not drivers:
            continue

        # car = next column
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

    # 🔥 dedupe (keep best row)
    by_finish = {}

    for r in results:
        f = r["finish"]

        if f not in by_finish:
            by_finish[f] = r
        else:
            if len(r["drivers"]) > len(by_finish[f]["drivers"]):
                by_finish[f] = r

    final_results = list(by_finish.values())
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
