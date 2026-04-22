import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("🏆 Scraping Davis Cup (WORKING VERSION)")

BASE_URL = "https://en.wikipedia.org/wiki/2024_Davis_Cup"

r = requests.get(BASE_URL)
soup = BeautifulSoup(r.text, "lxml")

matches = []

# Find ALL links to ties
links = soup.find_all("a")

tie_links = []

for a in links:
    href = a.get("href", "")
    if "/wiki/2024_Davis_Cup_" in href and "Group" not in href:
        tie_links.append("https://en.wikipedia.org" + href)

tie_links = list(set(tie_links))

print("Found ties:", len(tie_links))

for link in tie_links:
    print("→", link)

    r = requests.get(link)
    s = BeautifulSoup(r.text, "lxml")

    tables = s.find_all("table", {"class": "wikitable"})

    for table in tables:
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
