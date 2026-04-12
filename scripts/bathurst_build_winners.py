import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path

print("BATHURST WINNERS BUILDER (FINAL FIXED)")

URL = "https://en.wikipedia.org/wiki/Bathurst_1000"

OUT = Path("docs/data/bathurst/winners.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean(x):
    if not x:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)  # remove [a], [1] etc
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()

def split_drivers(text):
    if not text:
        return []
    return [clean(x) for x in re.split(r"/| and ", text) if clean(x)]

print("Fetching page...")
res = requests.get(URL, headers=HEADERS)

if res.status_code != 200:
    raise Exception("Failed to fetch page")

soup = BeautifulSoup(res.text, "html.parser")

print("Locating 'List of winners' section...")

# 🔥 find the correct section
header = None
for h in soup.find_all(["h2", "h3"]):
    if "List of winners" in h.get_text():
        header = h
        break

if header is None:
    raise Exception("❌ Winners section not found")

# 🔥 get the table directly after that section
table = header.find_next("table", {"class": "wikitable"})

if table is None:
    raise Exception("❌ Winners table not found")

rows = table.find_all("tr")[1:]

data = []

print(f"Processing {len(rows)} rows...")

for row in rows:
    cols = row.find_all("td")

    if len(cols) < 3:
        continue

    try:
        # 🔥 FIXED YEAR EXTRACTION
        year_text = clean(cols[0].get_text())
        match = re.search(r"\d{4}", year_text or "")
        if not match:
            continue

        year = int(match.group())

        drivers_raw = clean(cols[1].get_text())
        car = clean(cols[2].get_text())

        drivers = split_drivers(drivers_raw)

        if not drivers:
            continue

        data.append({
            "year": year,
            "drivers": drivers,
            "car": car
        })

    except Exception as e:
        print(f"⚠️ Skipped row: {e}")
        continue

# sort properly
data = sorted(data, key=lambda x: x["year"])

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE — saved {len(data)} years")
