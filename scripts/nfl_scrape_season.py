#!/usr/bin/env python3
"""
nfl_scrape_season.py

Scrapes a single NFL season from pro-football-reference.com and writes
data in the exact schema build_nfl_players.py already expects:

  docs/data/nfl/seasons/{season}.json
      { "season": int, "source": url, "updated": iso timestamp,
        "games": [ { "game_id", "date", "week", "team1", "team2",
                     "score1", "score2", "venue" }, ... ] }

  docs/data/nfl/boxscores/{season}/{game_id}.json
      { "game_id": str,
        "passing": [ {"player": name, "stats": {...}}, ... ],
        "rushing": [...], "receiving": [...], "defense": [...],
        "kicking": [...], "returns": [...], "scoring": [...] }

Usage:
    python3 scripts/nfl_scrape_season.py 2026

Only fetches boxscores for games that have already been played
(i.e. the boxscore page exists) and skips any boxscore file that's
already on disk, so it's safe to re-run weekly as the season goes on.
"""

import json
import os
import re
import sys
import time
import datetime as dt

import requests
from bs4 import BeautifulSoup, Comment

BASE = "https://www.pro-football-reference.com"

OUT_ROOT = "docs/data/nfl"
SEASONS_DIR = f"{OUT_ROOT}/seasons"
BOXSCORE_DIR = f"{OUT_ROOT}/boxscores"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch(url, retries=5):
    for i in range(retries):
        try:
            res = session.get(url, timeout=30)
            if "Just a moment" in res.text or res.status_code == 429:
                print(f"  blocked/rate-limited, retrying ({i+1}/{retries})...")
                time.sleep(8 + i * 4)
                continue
            if res.status_code == 200:
                return res.text
            if res.status_code == 404:
                return None
        except requests.RequestException as e:
            print(f"  request error: {e}, retrying...")
        time.sleep(3)
    return None


def find_table(soup, table_id):
    """PFR often ships tables inside HTML comments - check both places."""
    table = soup.find("table", {"id": table_id})
    if table:
        return table
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if f'id="{table_id}"' in c:
            inner = BeautifulSoup(c, "html.parser")
            t = inner.find("table", {"id": table_id})
            if t:
                return t
    return None


def parse_stat_table(table):
    """Return list of {"player": name, "stats": {col: value, ...}}"""
    rows = []
    if not table:
        return rows
    body = table.find("tbody")
    if not body:
        return rows
    for tr in body.find_all("tr"):
        if tr.get("class") and "thead" in tr.get("class"):
            continue
        name_cell = tr.find(["th", "td"], {"data-stat": "player"})
        if not name_cell:
            continue
        name = name_cell.get_text(strip=True)
        if not name or name.lower() in ("player", ""):
            continue
        stats = {}
        for cell in tr.find_all(["th", "td"]):
            key = cell.get("data-stat")
            if not key or key == "player":
                continue
            stats[key] = cell.get_text(strip=True)
        rows.append({"player": name, "stats": stats})
    return rows


def parse_scoring(table):
    entries = []
    if not table:
        return entries
    body = table.find("tbody")
    if not body:
        return entries
    for tr in body.find_all("tr"):
        cells = {c.get("data-stat"): c.get_text(strip=True) for c in tr.find_all(["th", "td"])}
        if not cells:
            continue
        entries.append({
            "quarter": cells.get("quarter", ""),
            "team": cells.get("team", ""),
            "scorer": cells.get("description", ""),
            "type": cells.get("score_type", ""),
            "description": cells.get("description", ""),
        })
    return entries


def get_schedule(season):
    url = f"{BASE}/years/{season}/games.htm"
    print(f"Fetching schedule: {url}")
    html = fetch(url)
    if not html:
        print("  FAILED to fetch schedule")
        return [], url

    soup = BeautifulSoup(html, "html.parser")
    table = find_table(soup, "games")
    games = []
    if not table:
        print("  no games table found (schedule likely not published yet)")
        return [], url

    body = table.find("tbody")
    if not body:
        return [], url

    week_counter = 0
    for tr in body.find_all("tr"):
        if tr.get("class") and "thead" in tr.get("class"):
            continue
        cells = {c.get("data-stat"): c for c in tr.find_all(["th", "td"])}
        if "boxscore_word" not in cells and "game_date" not in cells:
            continue

        box_link = None
        if "boxscore_word" in cells:
            a = cells["boxscore_word"].find("a", href=True)
            if a:
                box_link = a["href"]

        game_id = None
        if box_link:
            m = re.search(r"/boxscores/(.+)\.htm", box_link)
            if m:
                game_id = m.group(1)

        week = cells.get("week_num").get_text(strip=True) if cells.get("week_num") else ""
        date = cells.get("game_date").get_text(strip=True) if cells.get("game_date") else ""
        winner = cells.get("winner").get_text(strip=True) if cells.get("winner") else ""
        loser = cells.get("loser").get_text(strip=True) if cells.get("loser") else ""
        pts_w = cells.get("pts_win").get_text(strip=True) if cells.get("pts_win") else ""
        pts_l = cells.get("pts_lose").get_text(strip=True) if cells.get("pts_lose") else ""
        at_sym = cells.get("game_location").get_text(strip=True) if cells.get("game_location") else ""

        if not game_id:
            # Game not played yet (no boxscore link) - still record the fixture
            game_id = f"{season}_pending_{week}_{re.sub(r'[^a-z0-9]', '', winner.lower())}{re.sub(r'[^a-z0-9]', '', loser.lower())}"

        if at_sym == "@":
            team1, team2 = loser, winner
            score1, score2 = pts_l, pts_w
        else:
            team1, team2 = winner, loser
            score1, score2 = pts_w, pts_l

        games.append({
            "game_id": game_id,
            "date": date,
            "week": week,
            "team1": team1,
            "team2": team2,
            "score1": int(score1) if score1.isdigit() else None,
            "score2": int(score2) if score2.isdigit() else None,
            "venue": "",
            "_boxscore_url": (BASE + box_link) if box_link else None,
        })

    print(f"  found {len(games)} games")
    return games, url


def scrape_boxscore(game_id, url):
    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    return {
        "game_id": game_id,
        "passing": parse_stat_table(find_table(soup, "player_offense")),
        "rushing": parse_stat_table(find_table(soup, "player_offense")),
        "receiving": parse_stat_table(find_table(soup, "player_offense")),
        "defense": parse_stat_table(find_table(soup, "player_defense")),
        "kicking": parse_stat_table(find_table(soup, "kicking")),
        "returns": parse_stat_table(find_table(soup, "returns")),
        "scoring": parse_scoring(find_table(soup, "scoring")),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/nfl_scrape_season.py <season>")
        sys.exit(1)

    season = int(sys.argv[1])

    os.makedirs(SEASONS_DIR, exist_ok=True)
    box_dir = f"{BOXSCORE_DIR}/{season}"
    os.makedirs(box_dir, exist_ok=True)

    games, source_url = get_schedule(season)

    # Write seasons/{season}.json (strip internal _boxscore_url field)
    clean_games = [{k: v for k, v in g.items() if not k.startswith("_")} for g in games]
    season_out = {
        "season": season,
        "source": source_url,
        "updated": dt.datetime.utcnow().isoformat() + "Z",
        "games": clean_games,
    }
    with open(f"{SEASONS_DIR}/{season}.json", "w", encoding="utf-8") as f:
        json.dump(season_out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {SEASONS_DIR}/{season}.json ({len(clean_games)} games)")

    # Fetch boxscores for played games only, skipping ones already saved
    played = [g for g in games if g.get("_boxscore_url")]
    print(f"\n{len(played)} games have boxscores available")

    fetched, skipped, failed = 0, 0, 0
    for g in played:
        out_path = f"{box_dir}/{g['game_id']}.json"
        if os.path.exists(out_path):
            skipped += 1
            continue

        print(f"Fetching boxscore: {g['game_id']}")
        box = scrape_boxscore(g["game_id"], g["_boxscore_url"])
        if not box:
            print("  FAILED")
            failed += 1
            continue

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(box, f, indent=2, ensure_ascii=False)
        fetched += 1
        time.sleep(3)  # be polite to PFR

    print(f"\nDone. fetched={fetched} skipped(existing)={skipped} failed={failed}")


if __name__ == "__main__":
    main()
