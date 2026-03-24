import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import re
import time
from datetime import datetime

print("F1 2026 FINAL SCRAPER")

BASE = "https://www.formula1.com"
START_URL = "https://www.formula1.com/en/results/2026/races"

HEADERS = {"User-Agent": "Mozilla/5.0"}

OUTPUT = Path("docs/data/f1/2026.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# -----------------------------
# HELPERS
# -----------------------------
def get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print("ERROR:", url, e)
        return None


def clean_text(t):
    if not t:
        return ""
    t = t.replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def extract_driver(cell):
    spans = cell.select("span")

    if len(spans) >= 2:
        first = clean_text(spans[0].text)
        last = clean_text(spans[1].text)
        return f"{first} {last}"

    return clean_text(cell.text)


def clean_gp(text):
    text = clean_text(text)

    # remove FORMULA 1 branding + suffix
    text = re.sub(r"FORMULA 1 .*? GRAND PRIX", lambda m: m.group(0).split("GRAND PRIX")[0] + "Grand Prix", text)
    text = re.sub(r" – .*", "", text)

    return text.strip()


def slug_from_url(url):
    return url.split("/")[-2]


# -----------------------------
# GET RACE LINKS (FIXED)
# -----------------------------
print("Loading races...")

main = get_soup(START_URL)

race_links = []

for a in main.select("a[href]"):
    href = a["href"]

    if "/en/results/2026/races/" in href and "/race-result" in href:
        full = BASE + href
        if full not in race_links:
            race_links.append(full)

print("Races found:", len(race_links))


# -----------------------------
# BUILD DATA
# -----------------------------
season = {
    "season": 2026,
    "races": []
}

for race_url in race_links:

    print("\n---", race_url)

    race_soup = get_soup(race_url)
    if not race_soup:
        continue

    gp_name = clean_gp(race_soup.select_one("h1").text)
    slug = slug_from_url(race_url)

    # -------------------------
    # RESULTS
    # -------------------------
    results = []

    rows = race_soup.select("table tbody tr")

    if not rows:
        print("No results yet")
        continue

    for r in rows:

        tds = r.select("td")
        cols = [clean_text(c.text) for c in tds]

        if len(cols) < 7:
            continue

        try:
            pos = int(cols[0])
        except:
            continue

        driver = extract_driver(tds[2])

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

    if grid_soup:
        for r in grid_soup.select("table tbody tr"):
            tds = r.select("td")
            cols = [clean_text(c.text) for c in tds]

            if len(cols) < 3:
                continue

            try:
                pos = int(cols[0])
            except:
                continue

            driver = extract_driver(tds[2])
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

    if fl_soup:
        fl_rows = fl_soup.select("table tbody tr")

        if fl_rows:
            tds = fl_rows[0].select("td")
            cols = [clean_text(c.text) for c in tds]

            if len(cols) >= 5:
                fastest_driver = extract_driver(tds[2])
                fastest_time = cols[4]

    # -------------------------
    # SAVE RACE
    # -------------------------
    season["races"].append({
        "round": len(season["races"]) + 1,
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
    "races": season["races"]
}

with open(OUTPUT, "w") as f:
    json.dump(final, f, indent=2)

print("\nDONE:", len(season["races"]), "races saved")
