import json
import re
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

print("BATHURST WINNERS BUILDER (PANDAS FIX)")

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


def extract_year(value):
    text = clean(value)
    if not text:
        return None
    m = re.search(r"(19|20)\d{2}", text)
    if not m:
        return None
    return int(m.group(0))


def split_drivers(value):
    text = clean(value)
    if not text:
        return []

    text = text.replace(" / ", "/")
    text = text.replace(" and ", "/")
    parts = [clean(x) for x in text.split("/") if clean(x)]

    if len(parts) >= 2:
        return parts

    # fallback for badly merged names like "Bob Morris John Fitzpatrick"
    words = text.split()
    if len(words) == 4:
        return [" ".join(words[:2]), " ".join(words[2:])]
    if len(words) == 6:
        return [" ".join(words[:3]), " ".join(words[3:])]

    return [text]


print("Fetching page...")
res = requests.get(URL, headers=HEADERS, timeout=30)
res.raise_for_status()

print("Reading tables...")
tables = pd.read_html(StringIO(res.text))

target = None

for df in tables:
    cols = [clean(c) for c in df.columns]
    cols_lower = [c.lower() if c else "" for c in cols]

    has_year = any("year" == c or c.startswith("year") for c in cols_lower)
    has_driver = any("driver" in c for c in cols_lower)
    has_car = any("car" in c for c in cols_lower)

    if has_year and has_driver and has_car:
        target = df.copy()
        break

if target is None:
    raise RuntimeError("Could not find Bathurst winners table")

# normalise column names
rename_map = {}
for col in target.columns:
    c = clean(col)
    c_lower = c.lower() if c else ""

    if "year" in c_lower:
        rename_map[col] = "year"
    elif "driver" in c_lower:
        rename_map[col] = "drivers"
    elif "car" in c_lower:
        rename_map[col] = "car"

target = target.rename(columns=rename_map)

required = {"year", "drivers", "car"}
missing = required - set(target.columns)
if missing:
    raise RuntimeError(f"Missing expected columns: {sorted(missing)}")

results = []

for _, row in target.iterrows():
    year = extract_year(row.get("year"))
    if year is None or year < 1960 or year > 2100:
        continue

    drivers = split_drivers(row.get("drivers"))
    car = clean(row.get("car"))

    if not car:
        continue

    results.append({
        "year": year,
        "drivers": drivers,
        "car": car
    })

# dedupe by year, keep first good row
deduped = []
seen = set()

for item in sorted(results, key=lambda x: x["year"]):
    if item["year"] in seen:
        continue
    seen.add(item["year"])
    deduped.append(item)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(deduped, f, indent=2, ensure_ascii=False)

print(f"✅ DONE — saved {len(deduped)} years")
