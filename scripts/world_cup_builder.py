import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

print("🌍 WORLD CUP BUILDER STARTED")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

TOURNAMENTS = [
    {
        "year": 2023,
        "slug": "icc-cricket-world-cup-2023-1345038"
    }
]

def scrape_tournament(year, slug):

    print(f"➡️ Scraping {year}")

    url = f"https://www.espncricinfo.com/series/{slug}/match-results"
    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    matches = []

    # 🔥 UPDATED SELECTOR (WORKING)
    rows = soup.select("div.ds-p-4")

    for row in rows:

        teams = row.select("p.ds-text-tight-m")

        if len(teams) < 2:
            continue

        team1 = teams[0].text.strip()
        team2 = teams[1].text.strip()

        result_el = row.select_one("span.ds-text-tight-s")
        result = result_el.text.strip() if result_el else ""

        link = row.find("a", href=True)
        match_url = ""
        if link:
            match_url = "https://www.espncricinfo.com" + link["href"]

        matches.append({
            "team1": team1,
            "team2": team2,
            "result": result,
            "url": match_url,
            "year": year
        })

    print(f"✅ {year} matches found: {len(matches)}")

    # 🛑 FAIL SAFE
    if len(matches) == 0:
        print("❌ ERROR: No matches found — site structure likely changed")
        return []

    out_file = BASE / f"{year}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2)

    print(f"💾 Saved: {out_file}")

    return matches

def build_index(all_data):

    index = []

    for year, matches in all_data.items():
        index.append({
            "year": year,
            "matches": len(matches)
        })

    with open(BASE / "index.json", "w") as f:
        json.dump(index, f, indent=2)

    print("📚 Index built")

# -----------------------
# MAIN
# -----------------------
all_data = {}

for t in TOURNAMENTS:
    data = scrape_tournament(t["year"], t["slug"])
    if data:
        all_data[t["year"]] = data
    time.sleep(1)

if all_data:
    build_index(all_data)

print("🏁 DONE")
