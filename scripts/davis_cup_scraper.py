import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("🏆 Davis Cup scraper (stable version)")

URLS = [
    "https://en.wikipedia.org/wiki/2025_Davis_Cup_Qualifiers",
    "https://en.wikipedia.org/wiki/2025_Davis_Cup_World_Group_I",
    "https://en.wikipedia.org/wiki/2025_Davis_Cup_World_Group_II",
    "https://en.wikipedia.org/wiki/2025_Davis_Cup_Finals"
]

matches = []

for url in URLS:
    print("→", url)

    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")

    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            text = row.get_text(" ", strip=True)

            # look for match score pattern
            if "-" not in text:
                continue

            if len(text) < 10:
                continue

            if "/" in text:
                match_type = "Doubles"
            else:
                match_type = "Singles"

            matches.append({
                "text": text,
                "match_type": match_type,
                "event": "Davis Cup 2025"
            })

print("Matches found:", len(matches))

OUT = Path("docs/data/tennis/davis_cup/2025.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(matches, f, indent=2)

print("✅ Saved:", len(matches))
