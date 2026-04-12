import json
import re
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

print("BATHURST WINNERS BUILDER (STRUCTURE LOCKED)")

URL = "https://en.wikipedia.org/wiki/Bathurst_1000"
OUT = Path("docs/data/bathurst/winners.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


def clean(x):
    if x is None:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()


def extract_year(x):
    x = clean(x)
    if not x:
        return None
    m = re.search(r"(19|20)\d{2}", x)
    return int(m.group()) if m else None


def split_drivers(text):
    text = clean(text)
    if not text:
        return []

    text = text.replace(" / ", "/")
    text = text.replace(" and ", "/")

    parts = [clean(p) for p in text.split("/") if clean(p)]

    if len(parts) >= 2:
        return parts

    # fallback split
    words = text.split()
    if len(words) == 4:
        return [" ".join(words[:2]), " ".join(words[2:])]
    if len(words) == 6:
        return [" ".join(words[:3]), " ".join(words[3:])]

    return [text]


print("Fetching page...")
res = requests.get(URL, headers=HEADERS)
res.raise_for_status()

print("Reading ALL tables...")
tables = pd.read_html(StringIO(res.text))

print(f"Found {len(tables)} tables")

target = None

for df in tables:
    cols = [clean(c) for c in df.columns]
    cols_lower = [c.lower() if c else "" for c in cols]

    # 🔥 THIS matches EXACT structure in your screenshots
    if (
        any("year" in c for c in cols_lower)
        and any("driver" in c for c in cols_lower)
        and any("car" in c for c in cols_lower)
        and len(df) > 20  # real table, not small junk tables
    ):
        print("👉 FOUND CORRECT WINNERS TABLE")
        target = df.copy()
        break

if target is None:
    raise Exception("❌ Could not find winners table")

# normalize columns
rename = {}
for col in target.columns:
    c = clean(col).lower()

    if "year" in c:
        rename[col] = "year"
    elif "driver" in c:
        rename[col] = "drivers"
    elif "car" in c:
        rename[col] = "car"

target = target.rename(columns=rename)

results = []

for _, row in target.iterrows():
    year = extract_year(row.get("year"))
    if not year:
        continue

    if year < 1960 or year > 2100:
        continue

    drivers = split_drivers(row.get("drivers"))
    car = clean(row.get("car"))

    if not drivers or not car:
        continue

    results.append({
        "year": year,
        "drivers": drivers,
        "car": car
    })

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
