import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("🏏 LEGACY WORLD CUP SCRAPER (FINAL)")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

# -----------------------
# MATCH LIST (ADD MORE)
# -----------------------
MATCHES = [
    {
        "year": 1975,
        "match_id": "65035",
        "url": "https://www.espncricinfo.com/series/prudential-world-cup-1975-60793/england-vs-india-1st-match-65035/full-scorecard"
    }
]

# -----------------------
# FETCH PAGE (BLOCK DETECTION)
# -----------------------
def get_page(url):

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.espncricinfo.com/"
    }

    r = session.get(url, headers=headers)

    print("STATUS:", r.status_code)
    print("HTML SIZE:", len(r.text))

    # 🚨 BLOCK DETECTION
    if r.status_code != 200 or len(r.text) < 50000:
        print("❌ ESPN BLOCKED OR RETURNED LITE PAGE")
        return None

    return r.text

# -----------------------
# CLEAN TEXT
# -----------------------
def clean(text):
    return re.sub(r"\s+", " ", text.strip())

# -----------------------
# PARSE SCORECARD
# -----------------------
def parse_scorecard(html):

    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")

    print("TABLES FOUND:", len(tables))

    innings_data = []

    for i, table in enumerate(tables):

        rows = table.find_all("tr")

        if len(rows) < 5:
            continue

        batting = []

        for row in rows:

            cols = [c.get_text(strip=True) for c in row.find_all("td")]

            if len(cols) < 3:
                continue

            name = cols[0]

            if name.lower() in ["extras", "total"]:
                continue

            # detect batting rows (must have numbers)
            if any(char.isdigit() for char in "".join(cols[1:])):

                batting.append({
                    "player": name,
                    "raw": cols
                })

        if len(batting) > 5:
            print(f"✅ TABLE {i} = batting table ({len(batting)} players)")

            innings_data.append({
                "table_index": i,
                "batting": batting
            })

    return innings_data

# -----------------------
# MAIN LOOP
# -----------------------
for m in MATCHES:

    print("\n➡️ Scraping:", m["url"])

    html = get_page(m["url"])

    if not html:
        print("⚠️ Skipping due to block")
        continue

    innings = parse_scorecard(html)

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

    print("💾 Saved:", out_file)

print("\n🏁 DONE")
