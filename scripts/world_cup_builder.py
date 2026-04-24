import requests
from bs4 import BeautifulSoup
import json
import time

print("🌍 Scraping World Cup matches...")

BASE_URL = "https://www.espncricinfo.com/series/"
SERIES_ID = "icc-cricket-world-cup-2023-1345038"  # change per tournament

url = f"{BASE_URL}{SERIES_ID}/match-results"

r = requests.get(url)
soup = BeautifulSoup(r.text, "html.parser")

matches = []

cards = soup.select("div.ds-border-b.ds-border-line")

for card in cards:

    teams = card.select("p.ds-text-tight-m.ds-font-bold.ds-truncate")

    if len(teams) < 2:
        continue

    team1 = teams[0].text.strip()
    team2 = teams[1].text.strip()

    result = card.select_one("p.ds-text-tight-s.ds-font-regular.ds-truncate")

    score = result.text.strip() if result else ""

    link = card.find("a")
    match_url = "https://www.espncricinfo.com" + link["href"] if link else ""

    matches.append({
        "team1": team1,
        "team2": team2,
        "result": score,
        "url": match_url
    })

print(f"✅ Found {len(matches)} matches")

# SAVE
with open("world_cup_matches.json", "w") as f:
    json.dump(matches, f, indent=2)

print("💾 Saved to world_cup_matches.json")
