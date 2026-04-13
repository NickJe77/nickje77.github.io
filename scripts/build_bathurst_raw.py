import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
import re
import time

print("BUILDING BATHURST RAW DATASET")

OUT = Path("docs/data/bathurst/raw/bathurst_full.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if not x:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x or None


def split_drivers(text):
    text = clean(text) or ""
    parts = re.split(r"/|,| and | & |\+", text)

    out = []
    for p in parts:
        p = clean(p)
        if p and len(p.split()) >= 2:
            out.append(p)

    return out[:2]


def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500"
    ]

    for p in patterns:
        url = f"https://en.wikipedia.org/wiki/{p}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return url
        except:
            pass

    return None


def find_results_table(soup):
    for table in soup.find_all("table"):
        text = table.get_text(" ", strip=True).lower()
        if "driver" in text and ("pos" in text or "position" in text):
            return table
    return None


def parse_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return []

    print(f"Fetching {year}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        print(f"❌ Failed {year}")
        return []

    table = find_results_table(soup)

    if not table:
        print(f"❌ No table {year}")
        return []

    rows = []

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        ths = tr.find_all("th")

        if not tds:
            continue

        finish = None

        if ths:
            f = clean(ths[0].get_text())
            if f and f.isdigit():
                finish = int(f)

        if finish is None:
            f = clean(tds[0].get_text())
            if f and f.isdigit():
                finish = int(f)

        if finish is None:
            continue

        text = tr.get_text(" ", strip=True)

        drivers = split_drivers(text)

        # 🔥 FORCE 2 DRIVERS (temporary)
        if len(drivers) == 1:
            drivers.append("Unknown")

        if len(drivers) < 2:
            continue

        car = None
        for td in tds:
            c = clean(td.get_text())
            if c and c not in drivers and not c.isdigit():
                car = c
                break

        rows.append({
            "year": year,
            "finish": finish,
            "driver1": drivers[0],
            "driver2": drivers[1],
            "car": car or ""
        })

    return rows


# BUILD CSV
all_rows = []

for year in range(START_YEAR, END_YEAR + 1):
    data = parse_year(year)
    all_rows.extend(data)
    time.sleep(1)

# SORT
all_rows.sort(key=lambda x: (x["year"], x["finish"]))

# WRITE
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["year", "finish", "driver1", "driver2", "car"]
    )
    writer.writeheader()
    writer.writerows(all_rows)

print(f"🔥 DONE — {len(all_rows)} rows written")
