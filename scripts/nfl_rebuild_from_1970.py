#!/usr/bin/env python3
import os
import re
import json
import time
import random
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Comment

START_YEAR = 1970
END_YEAR = 1970   # test first

BASE = "https://www.pro-football-reference.com"
OUT_ROOT = "docs/data/nfl"
SEASONS_DIR = os.path.join(OUT_ROOT, "seasons")
BOXSCORES_DIR = os.path.join(OUT_ROOT, "boxscores")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
}

# -------------------------
# SETUP
# -------------------------
def mkdirs():
    os.makedirs(SEASONS_DIR, exist_ok=True)
    os.makedirs(BOXSCORES_DIR, exist_ok=True)

def get(url):
    print(f"GET {url}")
    r = requests.get(url, headers=HEADERS, timeout=30)

    time.sleep(random.uniform(4.0, 7.0))  # slow = avoid block

    if r.status_code != 200:
        print(f"  !! HTTP {r.status_code}")
        return None

    if "ad blocker" in r.text.lower():
        print("  !! BLOCKED BY PFR")
        return None

    print(f"  OK ({len(r.text)} bytes)")
    return r.text

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def to_int(v):
    try:
        return int(str(v).replace(",", "").strip())
    except:
        return None

# -------------------------
# 🔥 FIXED SCHEDULE PARSER
# -------------------------
def parse_schedule(year):
    url = f"{BASE}/years/{year}/games.htm"
    html = get(url)

    if not html:
        print("  !! NO HTML RETURNED")
        return []

    soup = BeautifulSoup(html, "html.parser")

    # 1️⃣ try normal table
    table = soup.find("table", id="games")
    if table:
        print("  ✅ found normal table")

    # 2️⃣ try comments
    if not table:
        print("  trying comment extraction...")
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))

        for c in comments:
            if "games" in c:
                try:
                    comment_soup = BeautifulSoup(c, "html.parser")
                    table = comment_soup.find("table", id="games")
                    if table:
                        print("  ✅ found table in comment")
                        break
                except:
                    continue

    if not table:
        print("  ❌ NO TABLE FOUND ANYWHERE")
        return []

    games = []

    rows = table.select("tbody tr")
    print(f"  rows found: {len(rows)}")

    for tr in rows:
        if "thead" in tr.get("class", []):
            continue

        cells = {}
        for td in tr.find_all(["th", "td"]):
            key = td.get("data-stat")
            if key:
                cells[key] = clean(td.get_text(" "))

        box_td = tr.find("td", {"data-stat": "boxscore_word"})
        a = box_td.find("a") if box_td else None

        if not a:
            continue

        box_url = urljoin(BASE, a.get("href"))
        game_id = os.path.basename(box_url).replace(".htm", "")

        games.append({
            "season": year,
            "game_id": game_id,
            "week": cells.get("week_num"),
            "date": cells.get("game_date"),
            "winner": cells.get("winner"),
            "loser": cells.get("loser"),
            "winner_points": to_int(cells.get("pts_win")),
            "loser_points": to_int(cells.get("pts_lose")),
            "boxscore_url": box_url,
            "boxscore_file": f"/data/nfl/boxscores/{year}/{game_id}.json"
        })

    print(f"  🎯 games parsed: {len(games)}")
    return games

# -------------------------
# SIMPLE BOXSCORE
# -------------------------
def parse_boxscore(game):
    year = game["season"]
    game_id = game["game_id"]

    out_dir = os.path.join(BOXSCORES_DIR, str(year))
    os.makedirs(out_dir, exist_ok=True)

    out_file = os.path.join(out_dir, f"{game_id}.json")

    if os.path.exists(out_file):
        return

    html = get(game["boxscore_url"])
    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""

    data = {
        "season": year,
        "game_id": game_id,
        "title": title,
        "source": game["boxscore_url"]
    }

    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  wrote boxscore {game_id}")

# -------------------------
# WRITE FILES
# -------------------------
def write_season(year, games):
    out_file = os.path.join(SEASONS_DIR, f"{year}.json")

    data = {
        "season": year,
        "source": f"{BASE}/years/{year}/games.htm",
        "updated": datetime.utcnow().isoformat() + "Z",
        "games": games
    }

    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"wrote {year}.json ({len(games)} games)")

# -------------------------
# MAIN
# -------------------------
def main():
    mkdirs()

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"\n===== NFL {year} =====")

        games = parse_schedule(year)

        for g in games:
            parse_boxscore(g)

        write_season(year, games)

    print("\nDONE")

if __name__ == "__main__":
    main()
