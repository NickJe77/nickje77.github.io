import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re

print("F1 2026 STRUCTURED SCRAPER")

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


def clean_gp_name(text):
    text = re.sub(r"Flag of .*? ", "", text)
    return text.strip()


def extract_slug(url):
    return url.split("/")[-2]


print("Loading races...")

soup = get_soup(START_URL)

race_links = []

for a in soup.select("a"):
    href = a.get("href", "")
    if "/en/results/2026/races/" in href and "race-result" in href:
        full = BASE + href
        if full not in race_links:
            race_links.append(full)

print("Races found:", len(race_links))


season_data = {
    "season": 2026,
    "races": []
}


for race_url in race_links:

    print("Scraping:", race_url)

    race_soup = get_soup(race_url)
    if not race_soup:
        continue

    # -----------------------
    # HEADER INFO
    # -----------------------
    try:
        header = race_soup.select_one("h1").text.strip()
        grand_prix = clean_gp_name(header)
    except:
        grand_prix = "Unknown"

    slug = extract_slug(race_url)

    # try to extract round
    round_num = None
    try:
        sub = race_soup.select_one("p")
        if sub:
            match = re.search(r"Round (\d+)", sub.text)
            if match:
                round_num = int(match.group(1))
    except:
        pass

    results_table = race_soup.select("table tbody tr")

    if not results_table:
        print("  → no results yet")
        continue

    race_results = []
    fastest_driver = None
    fastest_time = None

    for row in results_table:

        cols = [c.text.strip() for c in row.select("td")]

        if len(cols) < 7:
            continue

        try:
            position = int(cols[0])
        except:
            continue

        driver = cols[2]
        team = cols[3]
        laps = cols[4]
        time_val = cols[5]
        points = cols[6]

        race_results.append({
            "position": position,
            "driver": driver,
            "team": team,
            "grid": None,  # F1 site doesn't show grid here
            "time": time_val,
            "race_points": float(points) if points else 0,
            "sprint_points": 0,
            "points": float(points) if points else 0
        })

        # crude fastest lap detection (usually marked by fastest time)
        if "FL" in time_val or "fastest" in time_val.lower():
            fastest_driver = driver
            fastest_time = time_val

    season_data["races"].append({
        "round": round_num,
        "grand_prix": grand_prix,
        "race_id": None,
        "slug": slug,
        "fastest_lap_driver": fastest_driver,
        "fastest_lap_time": fastest_time,
        "results": race_results
    })


print("Races built:", len(season_data["races"]))

# FORCE UPDATE
final_output = {
    "season": 2026,
    "last_updated": str(__import__("datetime").datetime.utcnow()),
    "races": season_data["races"]
}

with open(OUTPUT, "w") as f:
    json.dump(final_output, f, indent=2)

print("SAVED:", OUTPUT)
