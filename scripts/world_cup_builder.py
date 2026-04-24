import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

print("🌍 WORLD CUP BUILDER STARTED")

# -----------------------
# OUTPUT DIR (FIXES YOUR ERROR)
# -----------------------
BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

# -----------------------
# TOURNAMENTS (ADD MORE HERE)
# -----------------------
TOURNAMENTS = [
    {
        "year": 2023,
        "slug": "icc-cricket-world-cup-2023-1345038"
    }
]

# -----------------------
# SCRAPER
# -----------------------
def scrape_tournament(year, slug):

    print(f"➡️ Scraping {year}")

    url = f"https://www.espncricinfo.com/series/{slug}/match-results"

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

        result_el = card.select_one("p.ds-text-tight-s.ds-font-regular.ds-truncate")
        result = result_el.text.strip() if result_el else ""

        link = card.find("a")
        match_url = ""
        if link:
            match_url = "https://www.espncricinfo.com" + link.get("href")

        matches.append({
            "team1": team1,
            "team2": team2,
            "result": result,
            "url": match_url,
            "year": year
        })

    print(f"✅ {year} matches found: {len(matches)}")

    # -----------------------
    # SAVE FILE
    # -----------------------
    out_file = BASE / f"{year}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2)

    print(f"💾 Saved: {out_file}")

    return matches

# -----------------------
# BUILD INDEX
# -----------------------
def build_index(all_data):

    index = []

    for year, matches in all_data.items():
        index.append({
            "year": year,
            "matches": len(matches)
        })

    index_file = BASE / "index.json"

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print("📚 Index built")

# -----------------------
# MAIN
# -----------------------
all_data = {}

for t in TOURNAMENTS:
    data = scrape_tournament(t["year"], t["slug"])
    all_data[t["year"]] = data
    time.sleep(1)

if all_data:
    build_index(all_data)

print("🏁 DONE")
