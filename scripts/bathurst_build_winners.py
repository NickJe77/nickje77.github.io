import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path

print("BATHURST WINNERS BUILDER (FIXED)")

URL = "https://en.wikipedia.org/wiki/Bathurst_1000#List_of_winners"

OUT = Path("docs/data/bathurst/winners.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def clean(x):
    if not x:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)  # remove [1], [a] etc
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()

def split_drivers(text):
    if not text:
        return []
    parts = re.split(r"/| and ", text)
    return [clean(p) for p in parts if clean(p)]

print("Fetching page...")

res = requests.get(URL, headers=HEADERS)
if res.status_code != 200:
    raise Exception(f"Failed to fetch page: {res.status_code}")

soup = BeautifulSoup(res.text, "html.parser")

print("Locating winners table...")

tables = soup.find_all("table", {"class": "wikitable"})

table = None
for t in tables:
    text = t.get_text()
    if "Year" in text and ("Driver" in text or "Drivers" in text):
        table = t
        break

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
        year_text = clean(cols[0].get_text())
        if not year_text or not year_text.isdigit():
            continue

        year = int(year_text)

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

# sort years just in case
data = sorted(data, key=lambda x: x["year"])

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE — saved {len(data)} years")
