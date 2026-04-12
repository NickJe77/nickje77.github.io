import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("BATHURST FULL SEASON BUILDER (NO PANDAS)")

URL = "https://en.wikipedia.org/wiki/Bathurst_1000#List_of_winners"

BASE = Path("docs/data/bathurst")
BASE.mkdir(parents=True, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}

res = requests.get(URL, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

tables = soup.find_all("table", {"class": "wikitable"})

if not tables:
    print("❌ No tables found")
    exit()

results_by_year = {}

def clean(text):
    text = re.sub(r"\[[^\]]*\]", "", text)
    return text.strip()

def extract_drivers(cell):
    links = cell.find_all("a")
    names = []

    for a in links:
        name = clean(a.get_text())
        if name and not name.startswith("File"):
            names.append(name)

    # fallback if no links
    if not names:
        raw = clean(cell.get_text())
        parts = re.split(r",|/| and ", raw)
        names = [p.strip() for p in parts if p.strip()]

    return names


for table in tables:

    rows = table.find_all("tr")[1:]

    for row in rows:
        cols = row.find_all(["td", "th"])

        if len(cols) < 5:
            continue

        try:
            year = int(clean(cols[0].get_text()))
        except:
            continue

        drivers = extract_drivers(cols[2])
        car = clean(cols[3].get_text())

        if year not in results_by_year:
            results_by_year[year] = []

        results_by_year[year].append({
            "finish": 1,  # only winners for now
            "grid": None,
            "drivers": drivers,
            "car": car,
            "laps": None
        })


# SAVE FILES PER YEAR
count = 0

for year, data in results_by_year.items():

    file = BASE / f"{year}.json"

    with open(file, "w") as f:
        json.dump({
            "year": year,
            "results": data
        }, f, indent=2)

    count += 1

print(f"✅ Built {count} seasons")
