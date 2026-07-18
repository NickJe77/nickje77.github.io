"""
Incremental NASCAR Cup Series updater
=============================
Unlike scrape_thirdturn_nascar.py (a one-time full backfill of 1949 to
present), this only touches the CURRENT season and only scrapes races
that aren't already in the saved JSON -- meant to run daily via GitHub
Actions without re-fetching the entire site's history every time.

Uses the season-index table on NASCAR_Cup_Series_Central (a single
lightweight fetch) to find the current year's hub page directly, then
compares that year's RACE LISTINGS against what's already saved.

Install:
  pip install requests beautifulsoup4

Run:
  python3 update_nascar_current.py --year 2026 --data-dir docs/data/nascar
"""

import argparse
import json
import os
import re
import time
import random

import requests
from bs4 import BeautifulSoup

BASE = "https://www.thethirdturn.com"
INDEX_PAGE = f"{BASE}/wiki/NASCAR_Cup_Series_Central"
MIN_SLEEP = 3
MAX_SLEEP = 6
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def get_soup(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                print(f"  WARNING: HTTP {resp.status_code} for {url}, attempt {attempt+1}/{retries}")
                print(f"    Response headers: {dict(resp.headers)}")
                print(f"    Body snippet: {resp.text[:300]!r}")
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"  WARNING: fetch failed ({e}), attempt {attempt+1}/{retries}")
            time.sleep(5)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")


def get_hub_url_for_year(year):
    print(f"GET {INDEX_PAGE}")
    soup = get_soup(INDEX_PAGE)
    tables = soup.find_all("table")

    index_table = None
    for t in tables:
        rows = t.find_all("tr")
        if rows:
            header = [clean(c.get_text()) for c in rows[0].find_all(["th", "td"])]
            if header[:2] == ["Season", "Races"]:
                index_table = t
                break

    if index_table is None:
        raise RuntimeError("Could not find the season-index table.")

    for row in index_table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if not cells:
            continue
        year_text = clean(cells[0].get_text())
        if year_text == str(year):
            links = row.find_all("a", href=True)
            if links:
                return BASE + links[0].get("href")

    return None


def parse_hub_page(url):
    soup = get_soup(url)
    tables = soup.find_all("table")

    listings_table = None
    for t in tables:
        rows = t.find_all("tr")
        if rows and clean(rows[0].get_text()) == "RACE LISTINGS":
            listings_table = t
            break

    races = []
    if listings_table:
        rows = listings_table.find_all("tr")
        for row in rows[2:]:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            links = row.find_all("a", href=True)
            race_href = links[0].get("href") if links else None
            race_url = (BASE + race_href) if race_href and race_href.startswith("/wiki/") else race_href
            races.append({
                "race_num": clean(cells[0].get_text()),
                "date": clean(cells[1].get_text()),
                "track_text": clean(cells[2].get_text()),
                "winner": clean(cells[3].get_text()),
                "url": race_url,
            })
    return races


def parse_race_page(url):
    soup = get_soup(url)
    tables = soup.find_all("table")

    title_tag = soup.find("title")
    title = clean(title_tag.get_text()) if title_tag else ""

    venue_text = ""
    distance_text = ""
    for t in tables:
        rows = t.find_all("tr")
        for row in rows:
            text = clean(row.get_text())
            if text.lower().startswith("held on"):
                venue_text = text
            elif "scheduled distance" in text.lower():
                distance_text = text

    results_table = None
    for t in tables:
        rows = t.find_all("tr")
        if not rows:
            continue
        header_cells = [clean(c.get_text()) for c in rows[0].find_all(["th", "td"])]
        if "Fin" in header_cells and "Driver" in header_cells:
            results_table = t
            break

    results = []
    if results_table:
        rows = results_table.find_all("tr")
        header = [clean(c.get_text()) for c in rows[0].find_all(["th", "td"])]
        for row in rows[1:]:
            cells = row.find_all(["th", "td"])
            texts = [clean(c.get_text()) for c in cells]
            if len(texts) < len(header):
                continue
            entry = dict(zip(header, texts))
            results.append(entry)

    return results, {
        "title": title,
        "venue_text": venue_text,
        "distance_text": distance_text,
        "url": url,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--data-dir", default="docs/data/nascar")
    args = ap.parse_args()

    out_path = os.path.join(args.data_dir, f"nascar_{args.year}.json")

    existing = {"year": args.year, "races": []}
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing = json.load(f)
    already_have = {str(r["race_num"]) for r in existing.get("races", [])}
    print(f"Already have {len(already_have)} race(s) for {args.year} saved.")

    hub_url = get_hub_url_for_year(args.year)
    if not hub_url:
        print(f"No hub page found for {args.year} yet (season may not have started). Nothing to do.")
        return

    print(f"Hub page: {hub_url}")
    all_races_meta = parse_hub_page(hub_url)
    print(f"{len(all_races_meta)} race(s) listed for {args.year}.")

    new_races = [r for r in all_races_meta if str(r["race_num"]) not in already_have and r["url"]]
    if not new_races:
        print("No new races found. Nothing to do.")
        return

    print(f"{len(new_races)} new race(s) to scrape.")
    added = []
    for i, r in enumerate(new_races, 1):
        print(f"  [{i}/{len(new_races)}] {r['date']} -- {r['winner']} -- {r['url']}")
        try:
            results, info = parse_race_page(r["url"])
        except Exception as e:
            print(f"    FAILED: {e}")
            continue
        if not results:
            print(f"    No results table yet (race may not have finished) -- skipping for now.")
            continue
        added.append({**r, "info": info, "results": results})
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))

    if not added:
        print("No races had results ready yet. Nothing to save.")
        return

    existing["races"] = existing.get("races", []) + added
    os.makedirs(args.data_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(added)} new race(s) -> {out_path} ({len(existing['races'])} total)")


if __name__ == "__main__":
    main()
