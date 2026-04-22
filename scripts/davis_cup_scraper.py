import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("🏆 Davis Cup scraper (tie-based)")

YEAR = "2024"

# Known tie pages (reliable approach instead of guessing links)
TIES = [
    "https://en.wikipedia.org/wiki/2024_Davis_Cup_Finals",
    "https://en.wikipedia.org/wiki/2024_Davis_Cup_Qualifiers",
]

matches = []

for url in TIES:
    print("→", url)

    r = requests.get(url)
    soup = BeautifulSoup(r.text, "lxml")

    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        rows = table.find_all("tr")

        for row in rows[1:]:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]

            if len(cols) < 3:
                continue

            p1 = cols[0]
            p2 = cols[1]
            score = cols[2]

            # detect doubles
            if "/" in p1 or "/" in p2:
                match_type = "Doubles"
            else:
                match_type = "Singles"

            matches.append({
                "player1": p1,
                "player2": p2,
                "score": score,
                "match_type": match_type,
                "event": "Davis Cup"
            })

print("Matches found:", len(matches))

OUT = Path(f"docs/data/tennis/davis_cup/{YEAR}.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(matches, f, indent=2)

print("✅ Saved:", OUT)
