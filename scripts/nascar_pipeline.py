"""
NASCAR pipeline: scrape current season from nascar.com, then rebuild
index.json / drivers.json. One file, does everything.

Combines the already-verified logic from scrape_nascar_official.py
(scraping) and build_nascar_official_index.py (index building) into a
single script, so automation only needs to call one thing.

Install:
  pip install undetected-chromedriver requests beautifulsoup4

Run:
  python3 nascar_pipeline.py --year 2026 --data-dir docs/data/nascar
"""

import argparse
import glob
import json
import os
import re
import time

import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

BASE = "https://www.nascar.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
SCHEDULE_WAIT_SECONDS = 8


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def extract_balanced_value(text, start_idx):
    opener = text[start_idx]
    if opener == "{":
        open_c, close_c = "{", "}"
    elif opener == "[":
        open_c, close_c = "[", "]"
    else:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start_idx, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return text[start_idx:i + 1]
    return None


def get_embedded_var(html, var_name):
    m = re.search(rf"const\s+{var_name}\s*=\s*([\[{{])", html)
    if not m:
        return None
    raw = extract_balanced_value(html, m.start(1))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


# ── Scraping ─────────────────────────────────────────────────────────

def get_season_race_urls(year):
    schedule_url = f"{BASE}/nascar-cup-series/{year}/schedule/"
    print(f"GET (browser) {schedule_url}")

    # CHROME_PATH, if set, points at the exact Chrome binary to use --
    # e.g. set by a CI workflow to whatever browser-actions/setup-chrome
    # actually installed. Avoids guessing a version_main number that only
    # happens to match one specific machine's Chrome (that broke this
    # exact way in CI: pinning to 150 -- correct on a local Mac -- didn't
    # match whatever "stable" resolved to on the GitHub Actions runner).
    chrome_path = os.environ.get("CHROME_PATH")

    for attempt in range(3):
        driver = None
        try:
            options = uc.ChromeOptions()
            options.add_argument("--window-size=1400,1000")
            if chrome_path:
                print(f"  Using explicit Chrome binary: {chrome_path}")
                driver = uc.Chrome(browser_executable_path=chrome_path, options=options)
            else:
                # Local/desktop use: no CHROME_PATH set, pin to the
                # confirmed real Chrome version on this machine -- update
                # via chrome://version if this ever breaks.
                driver = uc.Chrome(version_main=150, options=options)
            driver.set_page_load_timeout(120)

            driver.get(schedule_url)
            print(f"Waiting {SCHEDULE_WAIT_SECONDS}s for JS to populate the schedule...")
            time.sleep(SCHEDULE_WAIT_SECONDS)
            html = driver.page_source
            driver.quit()
            break
        except Exception as e:
            print(f"  Browser attempt {attempt + 1}/3 failed: {e}")
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            if attempt == 2:
                raise
            time.sleep(5)

    soup = BeautifulSoup(html, "html.parser")
    links = [a.get("href") for a in soup.find_all("a", href=True)
             if "live-results" in (a.get("href") or "")]

    seen = set()
    race_urls = []
    for l in links:
        base_url = l.split("?")[0]
        if not base_url.startswith("http"):
            base_url = BASE + base_url
        if base_url not in seen:
            seen.add(base_url)
            race_urls.append(base_url)

    print(f"Found {len(race_urls)} unique race URL(s) for {year}.")
    return race_urls


def scrape_race(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return get_embedded_var(resp.text, "weekendRaceData")


def scrape_season(year):
    race_urls = get_season_race_urls(year)
    if not race_urls:
        print("No race URLs found.")
        return []

    races = []
    for i, url in enumerate(race_urls, 1):
        print(f"[{i}/{len(race_urls)}] {url}")
        try:
            data = scrape_race(url)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue

        if not data:
            print(f"  No weekendRaceData found -- skipping (likely a future race).")
            continue

        # Future races' URLs still show LAST year's data until that
        # year's race actually happens -- confirmed real pattern (12 of
        # 37 scraped "2026" races were actually stale 2025 results).
        actual_season = data.get("race_season")
        if actual_season != year:
            print(f"  SKIPPING: this page's data is for {actual_season}, not {year}.")
            continue

        races.append({
            "url": url,
            "race_id": data.get("race_id"),
            "race_name": data.get("race_name"),
            "race_season": data.get("race_season"),
            "track_name": data.get("track_name"),
            "race_date": data.get("race_date"),
            "scheduled_laps": data.get("scheduled_laps"),
            "actual_laps": data.get("actual_laps"),
            "number_of_cautions": data.get("number_of_cautions"),
            "average_speed": data.get("average_speed"),
            "total_race_time": data.get("total_race_time"),
            "margin_of_victory": data.get("margin_of_victory"),
            "race_comments": data.get("race_comments"),
            "results": data.get("results", []),
        })
        print(f"  {data.get('race_name')} -- {len(data.get('results', []))} driver(s)")
        time.sleep(2)

    return races


# ── Index building ───────────────────────────────────────────────────

def load_season_files(data_dir):
    paths = sorted(glob.glob(os.path.join(data_dir, "nascar_official_*.json")))
    seasons = []
    for path in paths:
        m = re.search(r"nascar_official_(\d{4})\.json$", path)
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
            race_id = race.get("race_id")
            race_name = race.get("race_name")
            track_name = race.get("track_name")
            for result in race.get("results", []):
                name = (result.get("driver_fullname") or "").strip()
                if not name:
                    continue
                entry = drivers.setdefault(name, {"starts": 0, "wins": 0, "races": []})
                entry["starts"] += 1
                position = result.get("finishing_position")
                if position == 1:
                    entry["wins"] += 1
                car = " ".join(filter(None, [result.get("car_make"), result.get("car_model")]))
                entry["races"].append({
                    "year": year,
                    "race_id": race_id,
                    "race_name": race_name,
                    "track_name": track_name,
                    "finishing_position": position,
                    "starting_position": result.get("starting_position"),
                    "car_number": result.get("car_number"),
                    "team_name": result.get("team_name"),
                    "car": car,
                    "sponsor": result.get("sponsor"),
                    "laps_led": result.get("laps_led"),
                    "laps_completed": result.get("laps_completed"),
                    "finishing_status": result.get("finishing_status"),
                    "points_earned": result.get("points_earned"),
                })
    out = [{"name": n, "starts": e["starts"], "wins": e["wins"], "races": e["races"]}
           for n, e in drivers.items()]
    out.sort(key=lambda d: -d["wins"])
    return out


# ── Main ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--data-dir", default=".")
    args = ap.parse_args()

    os.makedirs(args.data_dir, exist_ok=True)
    out_path = os.path.join(args.data_dir, f"nascar_official_{args.year}.json")

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
