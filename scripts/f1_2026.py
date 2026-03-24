import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path

print("F1 2026 SCRAPER (OFFICIAL SITE)")

BASE = "https://www.formula1.com"
START_URL = "https://www.formula1.com/en/results/2026/races"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

OUTPUT = Path("docs/data/f1/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print("ERROR:", url, e)
        return None


print("Loading race list...")

soup = get_soup(START_URL)

if not soup:
    print("FAILED TO LOAD MAIN PAGE")
    exit()

# 🔥 FIND ALL RACE LINKS
race_links = []

for a in soup.select("a"):
    href = a.get("href", "")
    if "/en/results/2026/races/" in href and "race-result" in href:
        full = BASE + href
        if full not in race_links:
            race_links.append(full)

print("RACES FOUND:", len(race_links))


all_rows = []

# 🔥 LOOP RACES
for race_url in race_links:

    print("Scraping:", race_url)

    race_soup = get_soup(race_url)
    if not race_soup:
        continue

    # race name
    try:
        race_name = race_soup.select_one("h1").text.strip()
    except:
        race_name = "Unknown"

    # table rows
    rows = race_soup.select("table tbody tr")

    if not rows:
        print("  → no results yet")
        continue

    for row in rows:

        cols = [c.text.strip() for c in row.select("td")]

        if len(cols) < 7:
            continue

        try:
            position = int(cols[0])
        except:
            continue

        driver = cols[2]
        constructor = cols[3]
        laps = cols[4]
        time_val = cols[5]
        points = cols[6]

        all_rows.append({
            "season": 2026,
            "race_name": race_name,
            "position": position,
            "driver": driver,
            "constructor": constructor,
            "laps": laps,
            "time": time_val,
            "points": float(points) if points else 0
        })


print("TOTAL ROWS:", len(all_rows))

# 🔥 FORCE UPDATE
data = {
    "last_updated": str(__import__("datetime").datetime.utcnow()),
    "rows": all_rows
}

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print("SAVED:", OUTPUT)
