import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time

print("BATHURST FULL FIELD BUILDER (FINAL FIX)")

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


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


# 🔥 STEP 1: GET ALL RACE LINKS (NO GUESSING)
def get_links():
    url = "https://en.wikipedia.org/wiki/Bathurst_1000"
    res = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(res.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # find pages that look like race years
        if re.search(r"\d{4}.*(1000|500)", href):
            if href.startswith("/wiki/"):
                full = "https://en.wikipedia.org" + href
                links.append(full)

    return sorted(list(set(links)))


def fetch_page(url):
    year_match = re.search(r"(19|20)\d{2}", url)
    if not year_match:
        return None

    year = int(year_match.group(0))

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

    # dedupe
    unique = {}
    for r in results:
        key = (r["finish"], tuple(r["drivers"]))
        unique[key] = r

    final_results = list(unique.values())
    final_results.sort(key=lambda x: x["finish"])

    return year, final_results


# 🚀 RUN
links = get_links()
print(f"Found {len(links)} race pages")

built = 0

for link in links:
    data = fetch_page(link)

    if not data:
        continue

    year, results = data

    out = BASE / f"{year}.json"

    if out.exists():
        print(f"Skipping {year} (exists)")
        continue

    with open(out, "w") as f:
        json.dump({"year": year, "results": results}, f, indent=2)

    print(f"✅ Saved {year} ({len(results)} entries)")
    built += 1

    time.sleep(1)

print(f"🔥 BUILT {built} YEARS")
