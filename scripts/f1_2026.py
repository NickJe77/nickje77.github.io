import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time
from datetime import datetime

print("F1 2026 FINAL (CLEAN + CORRECT)")

BASE = "https://www.formula1.com"
START_URL = "https://www.formula1.com/en/results/2026/races"

HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT = Path("docs/data/f1/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# -----------------------------
# HELPERS
# -----------------------------
def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def clean_text(t):
    return re.sub(r"\s+", " ", t.replace("\xa0", " ")).strip()


def clean_driver(name):
    name = clean_text(name)

    # remove 3-letter suffix (VER, HAM, ANT)
    parts = name.split()
    if len(parts) >= 2 and len(parts[-1]) == 3:
        parts = parts[:-1]

    return " ".join(parts)


def extract_slug(href):
    # /en/results/2026/races/australia/race-result
    parts = href.split("/")
    if "races" in parts:
        i = parts.index("races")
        if i + 1 < len(parts):
            return parts[i + 1]
    return None


def clean_gp_from_slug(slug):
    return slug.replace("-", " ").title() + " Grand Prix"


# -----------------------------
# GET RACE LIST (CORRECT)
# -----------------------------
print("Loading race table...")

main = get_soup(START_URL)

race_links = []

for row in main.select("table tbody tr"):

    cols = row.select("td")
    if len(cols) < 2:
        continue

    try:
        round_num = int(cols[0].text.strip())
    except:
        continue

    a = row.select_one("a")
    if not a:
        continue

    href = a.get("href", "")

    if "/en/results/2026/races/" not in href:
        continue

    slug = extract_slug(href)

    race_links.append({
        "round": round_num,
        "slug": slug,
        "url": BASE + href + "/race-result"
    })

print("Races found:", len(race_links))


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

    print("\n---", slug, "Round", round_num)

    race_soup = get_soup(race_url)

    # ✅ GP NAME FROM SLUG (ALWAYS CORRECT)
    gp_name = clean_gp_from_slug(slug)

    # -------------------------
    # RESULTS
    # -------------------------
    results = []

    rows = race_soup.select("table tbody tr")

    if not rows:
        print("No results yet")
        continue

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
    grid_soup = get_soup(grid_url)

    grid_map = {}

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
    fl_soup = get_soup(fl_url)

    fastest_driver = None
    fastest_time = None

    fl_rows = fl_soup.select("table tbody tr")

    if fl_rows:
        cols = [clean_text(c.text) for c in fl_rows[0].select("td")]

        if len(cols) >= 5:
            fastest_driver = clean_driver(cols[2])
            fastest_time = cols[4]

    # -------------------------
    # SAVE
    # -------------------------
    season["races"].append({
        "round": round_num,
        "grand_prix": gp_name,
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
    "races": sorted(season["races"], key=lambda x: x["round"])
}

with open(OUTPUT, "w") as f:
    json.dump(final, f, indent=2)

print("\nDONE:", len(final["races"]), "races saved")
