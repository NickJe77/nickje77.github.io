import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("BATHURST WINNERS BUILDER (RAW HTML FIX)")

URL = "https://en.wikipedia.org/w/index.php?title=Bathurst_1000&printable=yes"

OUT = Path("docs/data/bathurst/winners.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def clean(x):
    if not x:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()


def extract_year(text):
    text = clean(text)
    if not text:
        return None
    m = re.search(r"(19|20)\d{2}", text)
    return int(m.group()) if m else None


def split_drivers(cell):
    # get linked names first (this matches your screenshot)
    links = [clean(a.get_text()) for a in cell.find_all("a") if clean(a.get_text())]

    if links:
        return links

    text = clean(cell.get_text())
    if not text:
        return []

    text = text.replace(" and ", "/")
    return [clean(x) for x in text.split("/") if clean(x)]


print("Fetching RAW printable page...")
res = requests.get(URL, headers=HEADERS, timeout=30)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")

print("Finding ALL wikitable tables...")
tables = soup.find_all("table", class_="wikitable")

print(f"Tables found: {len(tables)}")

target = None

# 🔥 Find the BIG Bathurst results table
for table in tables:
    rows = table.find_all("tr")

    if len(rows) < 50:
        continue

    header = " ".join(th.get_text() for th in table.find_all("th")).lower()

    if "year" in header and "driver" in header and "car" in header:
        target = table
        print("✅ FOUND MAIN TABLE")
        break

if target is None:
    raise Exception("❌ Could not find main results table")

results = []

for row in target.find_all("tr"):
    cols = row.find_all("td")

    # Must match your layout
    if len(cols) < 4:
        continue

    try:
        year = extract_year(cols[0].get_text())
        if not year or year < 1960:
            continue

        drivers = split_drivers(cols[2])
        car = clean(cols[3].get_text())

        if not drivers or not car:
            continue

        results.append({
            "year": year,
            "drivers": drivers,
            "car": car
        })

    except:
        continue

# remove duplicates
final = []
seen = set()

for r in sorted(results, key=lambda x: x["year"]):
    if r["year"] in seen:
        continue
    seen.add(r["year"])
    final.append(r)

with open(OUT, "w") as f:
    json.dump(final, f, indent=2)

print(f"✅ DONE — saved {len(final)} years")
