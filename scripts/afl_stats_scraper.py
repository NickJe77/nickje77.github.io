import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs

print("AFL SCRAPER (SAFE VERSION - NO DATA WIPE)")

SEASON = 2026
BASE = "https://www.footywire.com"
FIXTURE_URL = f"{BASE}/afl/footy/ft_match_list?year={SEASON}"

DATA_DIR = Path("docs/data/afl")
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEASON_FILE = DATA_DIR / f"afl_{SEASON}.json"

HEADERS = {"User-Agent": "Mozilla/5.0"}

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def clean(x):
    return re.sub(r"\s+", " ", (x or "")).strip()

def mid(url):
    return int(parse_qs(urlparse(url).query).get("mid", ["0"])[0])

def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

# -------------------------------------------------
# SCOREBOARD (STRICT + RELIABLE)
# -------------------------------------------------
def extract_scoreboard(soup):

    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")

        parsed = []

        for r in rows:
            cols = [clean(td.text) for td in r.find_all("td")]

            if len(cols) != 6:
                continue

            if not re.match(r"^\d+\.\d+$", cols[1]):
                continue

            if not cols[5].isdigit():
                continue

            parsed.append({
                "team": cols[0],
                "final": int(cols[5])
            })

        if len(parsed) == 2:
            return parsed[0], parsed[1]

    return None, None

# -------------------------------------------------
# SCRAPE MATCH
# -------------------------------------------------
def scrape_match(url):

    match_id = mid(url)

    try:
        soup = get_soup(url)
    except:
        print("FAILED LOAD:", match_id)
        return None

    home, away = extract_scoreboard(soup)

    if not home:
        print("SKIPPED (no scoreboard):", match_id)
        return None

    return {
        "match_id": match_id,
        "home_team": home["team"],
        "away_team": away["team"],
        "home_score": home["final"],
        "away_score": away["final"]
    }

# -------------------------------------------------
# RUN
# -------------------------------------------------
print("Fetching fixture...")

fixture = get_soup(FIXTURE_URL)

urls = list(set(
    urljoin(BASE, a["href"])
    for a in fixture.find_all("a", href=True)
    if "ft_match_statistics?mid=" in a["href"]
))

print(f"Found {len(urls)} matches")

new_data = []

for u in urls:
    result = scrape_match(u)
    if result:
        new_data.append(result)
    time.sleep(0.3)

print(f"Scraped {len(new_data)} valid matches")

# -------------------------------------------------
# SAFE SAVE
# -------------------------------------------------
if len(new_data) == 0:
    print("❌ NO DATA SCRAPED — NOT SAVING (PREVENT DATA WIPE)")
    exit()

# Load existing data if exists
if SEASON_FILE.exists():
    with open(SEASON_FILE) as f:
        old_data = json.load(f)
else:
    old_data = []

# Merge (no duplicates)
existing_ids = {m["match_id"] for m in old_data}

merged = old_data.copy()

added = 0

for m in new_data:
    if m["match_id"] not in existing_ids:
        merged.append(m)
        added += 1

print(f"Added {added} new matches")

# SAVE ONLY IF SAFE
with open(SEASON_FILE, "w") as f:
    json.dump(merged, f, indent=2)

print("✅ SAFE SAVE COMPLETE")
