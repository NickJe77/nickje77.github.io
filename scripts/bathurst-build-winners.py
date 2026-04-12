import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path

print("BATHURST WINNERS BUILDER")

URL = "https://en.wikipedia.org/wiki/Bathurst_1000#List_of_winners"

OUT = Path("docs/data/bathurst/winners.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

def clean(x):
    if not x:
        return None
    x = re.sub(r"\[[^\]]+\]", "", x)
    return x.strip()

def split_drivers(text):
    return [clean(x) for x in re.split(r"/| and ", text) if clean(x)]

res = requests.get(URL)
soup = BeautifulSoup(res.text, "html.parser")

table = soup.find("table", {"class": "wikitable"})
rows = table.find_all("tr")[1:]

data = []

for row in rows:
    cols = row.find_all("td")
    if len(cols) < 3:
        continue

    year = int(clean(cols[0].get_text()))
    drivers = split_drivers(clean(cols[1].get_text()))
    car = clean(cols[2].get_text())

    data.append({
        "year": year,
        "drivers": drivers,
        "car": car
    })

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"Saved {len(data)} winners")
