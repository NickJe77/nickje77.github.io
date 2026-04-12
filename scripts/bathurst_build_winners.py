import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path

print("BATHURST WINNERS BUILDER (ACTUAL FIX)")

URL = "https://en.wikipedia.org/wiki/Bathurst_1000"

OUT = Path("docs/data/bathurst/winners.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean(x):
    if not x:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()

def split_drivers(text):
    if not text:
        return []

    text = clean(text)

    # normal separators
    parts = re.split(r"/| and ", text)
    parts = [p.strip() for p in parts if p.strip()]

    # 🔥 if still one long string → force split
    if len(parts) == 1:
        words = parts[0].split()

        # assume 2 drivers → split in half
        if len(words) >= 4:
            mid = len(words) // 2
            parts = [
                " ".join(words[:mid]),
                " ".join(words[mid:])
            ]

    return parts

print("Fetching page...")
res = requests.get(URL, headers=HEADERS)

soup = BeautifulSoup(res.text, "html.parser")

# find correct section
header = None
for h in soup.find_all(["h2", "h3"]):
    if "List of winners" in h.get_text():
        header = h
        break

if header is None:
    raise Exception("No winners section")

table = header.find_next("table", {"class": "wikitable"})
rows = table.find_all("tr")[1:]

data = []

for row in rows:
    cols = row.find_all("td")
    if len(cols) < 3:
        continue

    try:
        # extract year
        year_text = clean(cols[0].get_text())
        match = re.search(r"\d{4}", year_text or "")
        if not match:
            continue

        year = int(match.group())

        # filter real Bathurst years
        if year < 1960 or year > 2100:
            continue

        drivers_raw = clean(cols[1].get_text())
        car = clean(cols[2].get_text())

        drivers = split_drivers(drivers_raw)

        # 🔥 DO NOT SKIP — always include
        data.append({
            "year": year,
            "drivers": drivers,
            "car": car
        })

    except:
        continue

data = sorted(data, key=lambda x: x["year"])

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ DONE — saved {len(data)} years")
