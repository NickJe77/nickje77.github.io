import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("🏆 Scraping Davis Cup (FINAL FIX)")

URL = "https://en.wikipedia.org/wiki/2024_Davis_Cup"

r = requests.get(URL)
soup = BeautifulSoup(r.text, "lxml")

matches = []

tables = soup.find_all("table")

for table in tables:

    headers = [th.get_text(strip=True) for th in table.find_all("th")]

    # Only tables that look like match tables
    if not any("Score" in h for h in headers):
        continue

    rows = table.find_all("tr")

    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        if len(cols) < 3:
            continue

        player_text = cols[0]

        # detect doubles
        if "/" in player_text:
            match_type = "Doubles"
            players = [p.strip() for p in player_text.split("/")]
        else:
            match_type = "Singles"
            players = [player_text]

        matches.append({
            "players": players,
            "opponent": cols[1],
            "score": cols[2],
            "match_type": match_type
        })

OUT = Path("docs/data/tennis/davis_cup/2024.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(matches, f, indent=2)

print("✅ Saved:", len(matches), "matches")
