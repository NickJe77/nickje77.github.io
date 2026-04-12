import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST FULL FIELD BUILDER (FORCED TABLE PARSE)")

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


# try multiple page names
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

    # 🔥 KEY FIX: find tables AFTER a results heading
    for header in soup.find_all(["h2", "h3"]):
        title = header.get_text().lower()

        if "result" in title or "classification" in title:
            table = header.find_next("table")

            if not table:
                continue

            for r in table.find_all("tr"):
                cols = [clean(c.get_text()) for c in r.find_all("td")]

                if len(cols) < 3:
                    continue

                try:
                    finish = int(cols[0])
                except:
                    continue

                # flexible column handling
                drivers_raw = None
                car = None

                if len(cols) >= 5:
                    drivers_raw = cols[2]
                    car = cols[3]
                else:
                    drivers_raw = cols[1]
                    car = cols[2] if len(cols) > 2 else None

                drivers = split_drivers(drivers_raw)

                if not drivers:
                    continue

                results.append({
                    "finish": finish,
                    "drivers": drivers,
                    "car": car
                })

            break  # stop after first valid results table

    if not results:
        print(f"⚠️ No results found {year}")
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
