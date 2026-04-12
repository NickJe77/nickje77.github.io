import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
from pathlib import Path
import re

print("BATHURST FULL HISTORY FIXED")

BASE = Path("docs/data/bathurst")
SEASONS = BASE / "seasons"
INDEX = BASE / "index.json"

SEASONS.mkdir(parents=True, exist_ok=True)

START_YEAR = 1960
END_YEAR = 2025  # adjust if needed

HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean(text):
    if not text:
        return None
    text = str(text)
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()

all_years = []

for year in range(START_YEAR, END_YEAR + 1):
    url = f"https://en.wikipedia.org/wiki/{year}_Bathurst_1000"

    print(f"Processing {year}...")

    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print(f"❌ Skipped {year}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        tables = soup.find_all("table", {"class": "wikitable"})
        target_table = None

        for table in tables:
            if "Driver" in table.text and "Class" not in table.text:
                target_table = table
                break

        if not target_table:
            print(f"❌ No results table {year}")
            continue

        df = pd.read_html(StringIO(str(target_table)))[0]

        drivers_cols = [c for c in df.columns if "Driver" in str(c)]

        season_data = []

        for _, row in df.iterrows():
            try:
                drivers = []

                for col in drivers_cols:
                    val = clean(row.get(col))
                    if val:
                        # split multiple drivers if needed
                        split = re.split(r"/|,| and ", val)
                        drivers.extend([clean(x) for x in split if x])

                drivers = list(dict.fromkeys(drivers))  # remove duplicates

                entry = {
                    "year": year,
                    "position": clean(row.get("Pos") or row.get("Position")),
                    "car": clean(row.get("Car")),
                    "team": clean(row.get("Team")),
                    "drivers": drivers
                }

                if not entry["drivers"]:
                    continue

                season_data.append(entry)

            except Exception as e:
                continue

        if not season_data:
            print(f"⚠️ No data extracted {year}")
            continue

        out_file = SEASONS / f"{year}.json"
        with open(out_file, "w") as f:
            json.dump(season_data, f, indent=2)

        all_years.append(year)
        print(f"✅ Saved {year}")

    except Exception as e:
        print(f"❌ Failed {year}: {e}")

# build index
with open(INDEX, "w") as f:
    json.dump(sorted(all_years), f, indent=2)

print("DONE")
