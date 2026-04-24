import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("🌍 WORLD CUP BUILDER (WIKI VERSION)")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

URL = "https://en.wikipedia.org/wiki/2023_Cricket_World_Cup"

r = requests.get(URL)
soup = BeautifulSoup(r.text, "html.parser")

matches = []

tables = soup.select("table.wikitable")

for table in tables:

    rows = table.find_all("tr")

    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all(["td","th"])]

        if len(cols) < 3:
            continue

        text = " ".join(cols)

        # crude but effective filter
        if "v" not in text.lower() and "beat" not in text.lower():
            continue

        matches.append({
            "text": text
        })

print("Matches found:", len(matches))

# -----------------------
# SAVE
# -----------------------
out_file = BASE / "2023.json"

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(matches, f, indent=2)

print("Saved:", out_file)
