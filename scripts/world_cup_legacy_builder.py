import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("🏏 DEBUG WORLD CUP SCRAPER")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

URL = "https://www.espncricinfo.com/series/prudential-world-cup-1975-60793/england-vs-india-1st-match-65035/full-scorecard"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(URL, headers=HEADERS)

print("STATUS:", r.status_code)
print("PAGE LENGTH:", len(r.text))

soup = BeautifulSoup(r.text, "html.parser")

tables = soup.find_all("table")

print("TABLES FOUND:", len(tables))

innings = []

for i, table in enumerate(tables):

    rows = table.find_all("tr")

    if len(rows) < 5:
        continue

    batting = []

    for row in rows:

        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        if len(cols) < 2:
            continue

        # try detect player rows
        name = cols[0]

        if name.lower() in ["extras", "total"]:
            continue

        # crude but effective: must have runs column
        if any(char.isdigit() for char in "".join(cols[1:])):

            batting.append({
                "player": name,
                "raw": cols
            })

    if len(batting) > 5:
        print(f"✅ TABLE {i} looks like batting table ({len(batting)} rows)")

        innings.append({
            "table_index": i,
            "batting": batting
        })

# -----------------------
# SAVE
# -----------------------
out_file = BASE / "1975_debug.json"

with open(out_file, "w") as f:
    json.dump(innings, f, indent=2)

print("💾 Saved debug file")
