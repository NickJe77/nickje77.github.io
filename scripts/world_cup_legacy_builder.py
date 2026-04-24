import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("🏏 LEGACY WORLD CUP SCRAPER (ESPN)")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# -----------------------
# ADD MATCHES HERE
# -----------------------
MATCHES = [
    {
        "year": 1975,
        "match_id": "65035",
        "url": "https://www.espncricinfo.com/series/prudential-world-cup-1975-60793/england-vs-india-1st-match-65035/full-scorecard"
    }
]

def clean(text):
    return re.sub(r"\s+", " ", text.strip())

def parse_scorecard(url):

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    innings_blocks = soup.select("div.ds-rounded-lg")

    innings_data = []

    for block in innings_blocks:

        title = block.find("span")
        if not title:
            continue

        team_name = clean(title.text)

        # -----------------------
        # BATTING TABLE
        # -----------------------
        batting = []

        rows = block.select("tbody tr")

        for row in rows:

            cols = [c.get_text(strip=True) for c in row.find_all("td")]

            if len(cols) < 8:
                continue

            batter = cols[0]
            runs = cols[2]
            balls = cols[3]
            fours = cols[5]
            sixes = cols[6]

            batting.append({
                "player": batter,
                "runs": runs,
                "balls": balls,
                "fours": fours,
                "sixes": sixes
            })

        # -----------------------
        # BOWLING TABLE
        # -----------------------
        bowling = []

        bowl_rows = block.select("table + table tbody tr")

        for row in bowl_rows:

            cols = [c.get_text(strip=True) for c in row.find_all("td")]

            if len(cols) < 5:
                continue

            bowling.append({
                "player": cols[0],
                "overs": cols[1],
                "runs": cols[3],
                "wickets": cols[4]
            })

        innings_data.append({
            "team": team_name,
            "batting": batting,
            "bowling": bowling
        })

    return innings_data

# -----------------------
# MAIN
# -----------------------
for m in MATCHES:

    print("➡️ Scraping", m["url"])

    try:
        innings = parse_scorecard(m["url"])

        match_data = {
            "match_id": m["match_id"],
            "year": m["year"],
            "innings": innings
        }

        year_path = BASE / str(m["year"])
        year_path.mkdir(parents=True, exist_ok=True)

        out_file = year_path / f"{m['match_id']}.json"

        with open(out_file, "w") as f:
            json.dump(match_data, f, indent=2)

        print("✅ Saved:", out_file)

    except Exception as e:
        print("❌ Failed:", e)

print("🏁 DONE")
