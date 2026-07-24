"""
Supercars pipeline: scrape current season from supercars.com, then
rebuild index.json / drivers.json. One file, does everything.

Combines the already-verified logic from scrape_supercars_official.py
(scraping) and build_supercars_official_index.py (index building) into
a single script, so automation only needs to call one thing.

No browser needed -- pure requests, unlike the NASCAR pipeline.

Install:
  pip install requests beautifulsoup4

Run:
  python3 supercars_pipeline.py --year 2026 --data-dir docs/data/supercars
"""

import argparse
import glob
import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup

BASE = "https://www.supercars.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
SLEEP_SECONDS = 2


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def get_soup(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


# ── Scraping ─────────────────────────────────────────────────────────

def get_season_race_urls(year):
    url = f"{BASE}/results/{year}/supercars"
    print(f"GET {url}")
    soup = get_soup(url)

    tables = soup.find_all("table")
    if not tables:
        print("  No results table found.")
        return []

    table = tables[0]
    rows = table.find_all("tr")

    seen = set()
    race_urls = []
    for row in rows[1:]:
        for a in row.find_all("a", href=True):
            text = clean(a.get_text())
            href = a.get("href")
            if "view race result" in text.lower() or re.search(r"/R\d+$", href or ""):
                full_url = href if href.startswith("http") else BASE + href
                if full_url not in seen:
                    seen.add(full_url)
                    race_urls.append(full_url)

    print(f"Found {len(race_urls)} unique race URL(s) for {year}.")
    return race_urls


def scrape_race(url):
    soup = get_soup(url)

    title_tag = soup.find("title")
    title = clean(title_tag.get_text()) if title_tag else ""
    parts = [clean(p) for p in title.split("|")]
    event_name = parts[2] if len(parts) > 2 else None
    race_label = parts[3] if len(parts) > 3 else None

    tables = soup.find_all("table")
    if not tables:
        return None, event_name, race_label

    table = tables[0]
    rows = table.find_all("tr")

    results = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        first_cell = cells[0]

        finish_pos = None
        pos_wrapper = first_cell.find("div", class_=re.compile(r"w-\[44px\]"))
        if pos_wrapper:
            pos_divs = [d for d in pos_wrapper.find_all("div") if clean(d.get_text())]
            if pos_divs:
                finish_pos = clean(pos_divs[0].get_text())

        car_number = None
        badge = first_cell.find("span")
        if badge:
            car_number = clean(badge.get_text())

        driver_name = None
        driver_href = None
        driver_link = first_cell.find("a", href=True)
        if driver_link:
            driver_name = clean(driver_link.get_text())
            driver_href = driver_link.get("href")

        team_name = None
        name_wrapper = first_cell.find("div", class_=re.compile(r"min-h-\[40px\]"))
        if name_wrapper:
            inner_divs = name_wrapper.find_all("div", recursive=False)
            if len(inner_divs) >= 2:
                team_name = clean(inner_divs[1].get_text())

        grid_pos = clean(cells[1].get_text()) if len(cells) > 1 else None
        race_time = clean(cells[2].get_text()) if len(cells) > 2 else None
        laps = clean(cells[3].get_text()) if len(cells) > 3 else None
        points = clean(cells[4].get_text()) if len(cells) > 4 else None

        if not driver_name:
            continue

        results.append({
            "finishing_position": finish_pos,
            "starting_position": grid_pos,
            "car_number": car_number,
            "driver_name": driver_name,
            "driver_url": (BASE + driver_href) if driver_href and driver_href.startswith("/") else driver_href,
            "team_name": team_name,
            "race_time": race_time,
            "laps": laps,
            "points": points,
        })

    return results, event_name, race_label


def scrape_season(year):
    race_urls = get_season_race_urls(year)
    if not race_urls:
        print("No race URLs found.")
        return []

    races = []
    for i, url in enumerate(race_urls, 1):
        print(f"[{i}/{len(race_urls)}] {url}")
        try:
            results, event_name, race_label = scrape_race(url)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue

        if not results:
            print(f"  No results found -- skipping.")
            continue

        races.append({
            "url": url,
            "event_name": event_name,
            "race_label": race_label,
            "results": results,
        })
        print(f"  {event_name} {race_label} -- {len(results)} driver(s)")
        time.sleep(SLEEP_SECONDS)

    return races


# ── Index building ───────────────────────────────────────────────────

def load_season_files(data_dir):
    paths = sorted(glob.glob(os.path.join(data_dir, "supercars_official_*.json")))
    seasons = []
    for path in paths:
        m = re.search(r"supercars_official_(\d{4})\.json$", path)
        if not m:
            continue
        year = int(m.group(1))
        with open(path, encoding="utf-8") as f:
            seasons.append((year, json.load(f)))
    seasons.sort(key=lambda x: x[0])
    return seasons


def build_index(seasons):
    return [{"year": year, "races": len(data.get("races", []))} for year, data in seasons]


def build_drivers(seasons):
    drivers = {}
    for year, data in seasons:
        for race in data.get("races", []):
            event_name = race.get("event_name")
            race_label = race.get("race_label")
            race_url = race.get("url")
            for result in race.get("results", []):
                name = (result.get("driver_name") or "").strip()
                if not name:
                    continue
                entry = drivers.setdefault(name, {
                    "starts": 0, "wins": 0, "races": [],
                    "driver_url": result.get("driver_url"),
                })
                entry["starts"] += 1
                position = result.get("finishing_position")
                if position == "1":
                    entry["wins"] += 1
                entry["races"].append({
                    "year": year,
                    "event_name": event_name,
                    "race_label": race_label,
                    "url": race_url,
                    "finishing_position": position,
                    "starting_position": result.get("starting_position"),
                    "car_number": result.get("car_number"),
                    "team_name": result.get("team_name"),
                    "race_time": result.get("race_time"),
                    "laps": result.get("laps"),
                    "points": result.get("points"),
                })
    out = [{"name": n, "driver_url": e["driver_url"], "starts": e["starts"],
            "wins": e["wins"], "races": e["races"]} for n, e in drivers.items()]
    out.sort(key=lambda d: -d["wins"])
    return out


# ── Main ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--data-dir", default=".")
    args = ap.parse_args()

    os.makedirs(args.data_dir, exist_ok=True)
    out_path = os.path.join(args.data_dir, f"supercars_official_{args.year}.json")

    print("=" * 60)
    print(f"STEP 1: Scrape {args.year}")
    print("=" * 60)
    races = scrape_season(args.year)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"year": args.year, "races": races}, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(races)} race(s) -> {out_path}")

    print("\n" + "=" * 60)
    print("STEP 2: Rebuild index.json + drivers.json")
    print("=" * 60)
    seasons = load_season_files(args.data_dir)
    if not seasons:
        print("No season files found -- skipping index rebuild.")
        return

    index = build_index(seasons)
    with open(os.path.join(args.data_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"Wrote index.json ({len(index)} season(s))")

    drivers = build_drivers(seasons)
    with open(os.path.join(args.data_dir, "drivers.json"), "w", encoding="utf-8") as f:
        json.dump(drivers, f, indent=2, ensure_ascii=False)
    print(f"Wrote drivers.json ({len(drivers)} driver(s))")
    if drivers:
        print(f"Most wins: {drivers[0]['name']} ({drivers[0]['wins']} wins)")


if __name__ == "__main__":
    main()
