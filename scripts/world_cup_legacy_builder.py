import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("🏏 LEGACY WORLD CUP SCRAPER (FINAL)")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# -----------------------
# ADD MATCHES HERE (TEST ONE FIRST)
# -----------------------
MATCHES = [
    {
        "year": 1975,
        "match_id": "65035",
        "url": "https://www.espncricinfo.com/series/prudential-world-cup-1975-60793/england-vs-india-1st-match-65035/full-scorecard"
    }
]

# -----------------------
# CLEAN TEXT
# -----------------------
def clean(text):
    return re.sub(r"\s+", " ", text.strip())

# -----------------------
# PARSE SCORECARD
# -----------------------
def parse_scorecard(url):

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("❌ Failed to fetch:", r.status_code)
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    innings_data = []

    # 🔥 ALL TABLES
    tables = soup.select("table")

    for table in tables:

        # find innings title above table
        header = table.find_previous(["span", "h2", "h3"])
        if not header:
            continue

        team_name = clean(header.text)

        # only pick innings tables (avoid junk)
        if "innings" not in team_name.lower():
            continue

        # -----------------------
        # BATTING
        # -----------------------
        batting = []

        rows = table.find_all("tr")

        for row in rows:

            cols = [c.get_text(strip=True) for c in row.find_all("td")]

            # batting rows typically 8+ columns
            if len(cols) < 7:
                continue

            player = cols[0]

            # skip extras/total rows
            if player.lower() in ["extras", "total"]:
                continue

            batting.append({
                "player": player,
                "runs": cols[2] if len(cols) > 2 else "",
                "balls": cols[3] if len(cols) > 3 else "",
                "fours": cols[5] if len(cols) > 5 else "",
                "sixes": cols[6] if len(cols) > 6 else ""
            })

        # -----------------------
        # BOWLING (NEXT TABLE)
        # -----------------------
        bowling = []

        next_table = table.find_next("table")

        if next_table:
            for row in next_table.find_all("tr"):

                cols = [c.get_text(strip=True) for c in row.find_all("td")]

                if len(cols) < 5:
                    continue

                bowling.append({
                    "player": cols[0],
                    "overs": cols[1],
                    "runs": cols[3],
                    "wickets": cols[4]
                })

        if batting:
            innings_data.append({
                "team": team_name,
                "batting": batting,
                "bowling": bowling
            })

    return innings_data

# -----------------------
# MAIN LOOP
# -----------------------
for m in MATCHES:

    print("➡️ Scraping:", m["url"])

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

print("🏁 DONE")
