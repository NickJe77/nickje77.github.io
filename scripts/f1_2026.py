import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time
from datetime import datetime

print("F1 2026 FINAL WORKING SCRIPT")

BASE = "https://www.formula1.com"
START_URL = "https://www.formula1.com/en/results/2026/races"

HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT = Path("docs/data/f1/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# -----------------------------
# HELPERS
# -----------------------------
def get_html(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text


def get_soup(url):
    return BeautifulSoup(get_html(url), "html.parser")


def clean_text(t):
    return re.sub(r"\s+", " ", t.replace("\xa0", " ")).strip()


def clean_driver(name):
    name = clean_text(name)
    parts = name.split()

    # remove 3-letter code
    if len(parts) >= 2 and len(parts[-1]) == 3:
        parts = parts[:-1]

    return " ".join(parts)


def clean_gp(slug):
    return slug.replace("-", " ").title() + " Grand Prix"


# -----------------------------
# GET RACE SLUGS (FIXED)
# -----------------------------
print("Extracting race slugs...")

html = get_html(START_URL)

matches = re.findall(r'/en/results/2026/races/([a-z-]+)/race-result', html)

# keep order
seen = set()
slugs = []
for m in matches:
    if m not in seen:
        seen.add(m)
        slugs.append(m)

print("Slugs found:", slugs)


race_links = []

for i, slug in enumerate(slugs, start=1):
    race_links.append({
        "round": i,
        "slug": slug,
        "url": f"{BASE}/en/results/2026/races/{slug}/race-result"
    })

print("Races built:", len(race_links))


# -----------------------------
# BUILD DATA
# -----------------------------
season = {
    "season": 2026,
    "races": []
}

for race in race_links:

    round_num = race["round"]
    slug = race["slug"]
    race_url = race["url"]

    print("\n---", slug)

    try:
        race_soup = get_soup(race_url)
    except:
        print("Skipping bad URL:", race_url)
        continue

    rows = race_soup.select("table tbody tr")

    if not rows:
        print("No results yet → skipping")
        continue

    results = []

    for r in rows:
        cols = [clean_text(c.text) for c in r.select("td")]

        if len(cols) < 7:
            continue

        try:
            pos = int(cols[0])
        except:
            continue

        driver = clean_driver(cols[2])

        results.append({
            "position": pos,
            "driver": driver,
            "team": cols[3],
            "grid": None,
            "time": cols[5],
            "race_points": float(cols[6]) if cols[6] else 0,
            "sprint_points": 0,
            "points": float(cols[6]) if cols[6] else 0
        })

    # -------------------------
    # GRID
    # -------------------------
    grid_url = race_url.replace("race-result", "starting-grid")

    try:
        grid_soup = get_soup(grid_url)
    except:
        grid_soup = None

    grid_map = {}

    if grid_soup:
        for r in grid_soup.select("table tbody tr"):
            cols = [clean_text(c.text) for c in r.select("td")]

            if len(cols) < 3:
                continue

            try:
                pos = int(cols[0])
            except:
                continue

            driver = clean_driver(cols[2])
            grid_map[driver] = pos

    for r in results:
        r["grid"] = grid_map.get(r["driver"])

    # -------------------------
    # FASTEST LAP
    # -------------------------
    fl_url = race_url.replace("race-result", "fastest-laps")

    fastest_driver = None
    fastest_time = None

    try:
        fl_soup = get_soup(fl_url)
        fl_rows = fl_soup.select("table tbody tr")

        if fl_rows:
            cols = [clean_text(c.text) for c in fl_rows[0].select("td")]

            if len(cols) >= 5:
                fastest_driver = clean_driver(cols[2])
                fastest_time = cols[4]
    except:
        pass

    # -------------------------
    # SAVE
    # -------------------------
    season["races"].append({
        "round": round_num,
        "grand_prix": clean_gp(slug),
        "race_id": None,
        "slug": slug,
        "fastest_lap_driver": fastest_driver,
        "fastest_lap_time": fastest_time,
        "results": results
    })

    time.sleep(0.4)


# -----------------------------
# SAVE FILE
# -----------------------------
final = {
    "season": 2026,
    "last_updated": datetime.utcnow().isoformat(),
    "races": season["races"]
}

with open(OUTPUT, "w") as f:
    json.dump(final, f, indent=2)

print("\nDONE:", len(final["races"]), "races saved")
