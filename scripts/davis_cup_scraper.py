import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("🏆 Scraping Davis Cup (WITH DOUBLES)")

URL = "https://en.wikipedia.org/wiki/2024_Davis_Cup"

r = requests.get(URL)
soup = BeautifulSoup(r.text, "lxml")

matches = []

tables = soup.find_all("table", {"class": "wikitable"})

for table in tables:
    rows = table.find_all("tr")

    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all(["td","th"])]

        if len(cols) < 3:
            continue

        players = cols[0]

        if "/" in players:
            match_type = "Doubles"
            players_list = [p.strip() for p in players.split("/")]
        else:
            match_type = "Singles"
            players_list = [players]

        matches.append({
            "players": players_list,
            "opponent": cols[1] if len(cols) > 1 else "",
            "score": cols[2] if len(cols) > 2 else "",
            "match_type": match_type
        })

OUT = Path("docs/data/tennis/davis_cup/2024.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUT, "w") as f:
    json.dump(matches, f, indent=2)

print("✅ Saved:", OUT)
