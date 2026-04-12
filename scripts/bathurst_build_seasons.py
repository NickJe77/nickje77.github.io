import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST FULL FIELD BUILDER (FINAL WORKING)")

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


def fetch_year(year):
    url = f"https://en.wikipedia.org/wiki/{year}_Bathurst_1000"

    print(f"Fetching {year}...")
    res = requests.get(url, headers=HEADERS)
    print(f"STATUS {year}: {res.status_code}")

    if res.status_code != 200:
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    results = []

    tables = soup.find_all("table", {"class": "wikitable"})

    for table in tables:
        headers = [clean(th.get_text()) for th in table.find_all("th")]
        if not headers:
            continue

        header_str = " ".join(headers).lower()

        if "position" in header_str or "pos" in header_str:
            for r in table.find_all("tr"):
                cols = [clean(c.get_text()) for c in r.find_all("td")]

                if len(cols) < 3:
                    continue

                try:
                    finish = int(cols[0])
                except:
                    continue

                drivers_raw = cols[2] if len(cols) >= 5 else cols[1]
                car = cols[3] if len(cols) >= 4 else None

                drivers = split_drivers(drivers_raw)

                if not drivers:
                    continue

                results.append({
                    "finish": finish,
                    "drivers": drivers,
                    "car": car
                })

    if not results:
        print(f"⚠️ No results {year}")
        return None

    # remove duplicates
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

    # ✅ ALWAYS WRITE (this was your issue)
    with open(out, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved {y} ({len(data['results'])} entries)")
    built += 1

    time.sleep(1)

print(f"🔥 BUILT {built} YEARS")
