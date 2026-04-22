import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("🏆 Davis Cup scraper (clean version)")

URLS = [
    "https://en.wikipedia.org/wiki/2025_Davis_Cup_Qualifiers",
    "https://en.wikipedia.org/wiki/2025_Davis_Cup_World_Group_I",
    "https://en.wikipedia.org/wiki/2025_Davis_Cup_World_Group_II",
    "https://en.wikipedia.org/wiki/2025_Davis_Cup_Finals"
]

matches = []

score_pattern = re.compile(r"\d-\d")

for url in URLS:
    print("→", url)

    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")

    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]

            if len(cols) < 3:
                continue

            player1 = cols[0]
            player2 = cols[1]
            score = cols[2]

            # must look like a tennis score
            if not score_pattern.search(score):
                continue

            # detect doubles
            if "/" in player1 or "/" in player2:
                match_type = "Doubles"
            else:
                match_type = "Singles"

            matches.append({
                "player1": player1,
                "player2": player2,
                "score": score,
                "match_type": match_type,
                "event": "Davis Cup 2025"
            })

print("Matches found:", len(matches))

OUT = Path("docs/data/tennis/davis_cup/2025.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(matches, f, indent=2)

print("✅ Saved:", len(matches))
