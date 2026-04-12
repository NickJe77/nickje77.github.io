import json
import re
from pathlib import Path
from io import StringIO

import pandas as pd
import requests

print("BATHURST FULL SEASON BUILDER")

BASE = Path("docs/data/bathurst/seasons")
BASE.mkdir(parents=True, exist_ok=True)

URL = "https://en.wikipedia.org/wiki/Bathurst_1000"

def clean(x):
    if x is None: return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()

def extract_year(x):
    m = re.search(r"(19|20)\d{2}", str(x))
    return int(m.group()) if m else None

print("Fetching tables...")
html = requests.get(URL).text
tables = pd.read_html(StringIO(html))

print(f"{len(tables)} tables found")

for df in tables:

    cols = [clean(c).lower() for c in df.columns]

    # 🔥 detect FULL RESULTS tables
    if not any("position" in c or "pos" in c for c in cols):
        continue

    if not any("driver" in c for c in cols):
        continue

    if not any("car" in c for c in cols):
        continue

    print("Processing table...")

    for _, row in df.iterrows():

        try:
            year = extract_year(row.iloc[0])
            if not year:
                continue

            finish = int(row.iloc[1]) if str(row.iloc[1]).isdigit() else None
            drivers_raw = clean(row.iloc[2])
            car = clean(row.iloc[3])

            drivers = [d.strip() for d in re.split(r"/| and ", drivers_raw) if d.strip()]

            if not drivers:
                continue

            season_file = BASE / f"{year}.json"

            if season_file.exists():
                data = json.load(open(season_file))
            else:
                data = {"year": year, "results": []}

            data["results"].append({
                "finish": finish,
                "drivers": drivers,
                "car": car
            })

            with open(season_file, "w") as f:
                json.dump(data, f, indent=2)

        except:
            continue

print("DONE")
