import json
import re
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

print("BATHURST WINNERS BUILDER (LOCKED TO WINNERS SECTION)")

URL = "https://en.wikipedia.org/wiki/Bathurst_1000"
OUT = Path("docs/data/bathurst/winners.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def clean(text):
    if text is None:
        return None
    text = str(text)
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def split_drivers(text):
    text = clean(text)
    if not text:
        return []

    text = text.replace(" / ", "/")
    text = text.replace(" and ", "/")
    parts = [clean(x) for x in text.split("/") if clean(x)]

    if len(parts) >= 2:
        return parts

    # fallback for cases where names may be merged oddly
    words = text.split()
    if len(words) == 4:
        return [" ".join(words[:2]), " ".join(words[2:])]
    if len(words) == 6:
        return [" ".join(words[:3]), " ".join(words[3:])]

    return [text]


print("Fetching page...")
res = requests.get(URL, headers=HEADERS, timeout=30)
res.raise_for_status()

soup = BeautifulSoup(res.text, "html.parser")

print("Locating exact 'List of winners' section...")
anchor = soup.find(id="List_of_winners")
if anchor is None:
    raise RuntimeError("Could not find 'List_of_winners' section on page")

table = anchor.find_parent(["h2", "h3"]).find_next("table", class_="wikitable")
if table is None:
    raise RuntimeError("Could not find winners table after 'List_of_winners' section")

print("Reading exact winners table...")
dfs = pd.read_html(StringIO(str(table)))
if not dfs:
    raise RuntimeError("pandas could not read winners table")

df = dfs[0].copy()

# Flatten any multi-index columns just in case
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [
        " ".join([clean(part) for part in col if clean(part)]).strip()
        for col in df.columns
    ]
else:
    df.columns = [clean(c) for c in df.columns]

# Find the right columns from the exact table
year_col = None
drivers_col = None
car_col = None

for col in df.columns:
    cl = (col or "").lower()
    if year_col is None and "year" in cl:
        year_col = col
    elif drivers_col is None and "driver" in cl:
        drivers_col = col
    elif car_col is None and "car" in cl:
        car_col = col

if year_col is None or drivers_col is None or car_col is None:
    raise RuntimeError(
        f"Could not identify required columns. Found columns: {list(df.columns)}"
    )

results = []

for _, row in df.iterrows():
    year_text = clean(row.get(year_col))
    if not year_text:
        continue

    m = re.search(r"(19|20)\d{2}", year_text)
    if not m:
        continue

    year = int(m.group(0))
    if year < 1960 or year > 2100:
        continue

    drivers = split_drivers(row.get(drivers_col))
    car = clean(row.get(car_col))

    if not drivers or not car:
        continue

    results.append({
        "year": year,
        "drivers": drivers,
        "car": car
    })

# Deduplicate by year, keeping first occurrence from the winners table
final = []
seen = set()

for item in sorted(results, key=lambda x: x["year"]):
    if item["year"] in seen:
        continue
    seen.add(item["year"])
    final.append(item)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(final, f, indent=2, ensure_ascii=False)

print(f"✅ DONE — saved {len(final)} years")
