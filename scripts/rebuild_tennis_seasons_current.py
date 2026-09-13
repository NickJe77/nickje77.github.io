#!/usr/bin/env python3
"""
rebuild_tennis_seasons_current.py  (tennis-db.com version)

UNTESTED — see note below.

Every previous source failed for a different reason:
  - tennis-data.co.uk: blocks automated requests (403)
  - JeffSackmann/tennis_atp: repo no longer exists (404)
  - Aneeshers/tennis-sackmann-archive: real, but frozen at the French Open
  - api-tennis.com: could not get a working key

tennis-db.com has real, current data (verified by hand for the US Open and
Wimbledon). Its AI-preview endpoint (matches.md) deliberately caps at 20
rows per page, but its own metadata states the *real* page
(https://tennis-db.com/matches, no .md) shows 200 rows per page. This
script targets that real page on the assumption a plain HTTP GET returns
the same full table. That assumption has NOT been verified against the
live site or from a real GitHub Actions run — I have no way to reach this
domain from my own environment to test it first.

If this fails, the two most likely causes, in order:
  1. The site blocks non-browser traffic (same problem as before) — the
     log will show a non-200 status or a "Just a moment"-style block.
  2. The HTML table structure differs from what BeautifulSoup expects
     here — the log will show 0 matches parsed despite a 200 response.

Either failure mode will be visible in stdout. Please paste the log back
if it doesn't work — I'd rather fix the actual error than guess again.

Usage:
    python3 scripts/rebuild_tennis_seasons_current.py
"""

import json
import os
import re
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

BASE = "docs/data/tennis/seasons"
CURRENT_YEAR = date.today().year
PREV_YEAR = CURRENT_YEAR - 1

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
}

TOUR_URLS = {
    "M": "https://tennis-db.com/matches",
    "F": "https://tennis-db.com/wta/matches",
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch_page(tour, season, page):
    url = TOUR_URLS[tour]
    params = {"season": season, "page": page}
    r = session.get(url, params=params, timeout=30)
    print(f"  GET {r.url} -> {r.status_code}, {len(r.content)} bytes")
    if r.status_code != 200:
        return None
    return r.text


def parse_rows(html, gender):
    soup = BeautifulSoup(html, "html.parser")
    matches = []

    table = soup.find("table")
    if not table:
        print("  no <table> found in response")
        return matches

    current_round = ""
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        text = row.get_text(" ", strip=True)

        # round header rows look like "F (1)" or "R32 (16)" with no <td>s
        if len(cells) < 2:
            m = re.match(r"^([A-Z0-9]+)\s*\(\d+\)$", text)
            if m:
                current_round = m.group(1)
            continue

        try:
            winner = cells[0].get_text(" ", strip=True)
            score = cells[1].get_text(" ", strip=True)
            loser = cells[2].get_text(" ", strip=True)
            date_txt = cells[-2].get_text(" ", strip=True)
        except IndexError:
            continue

        if not winner or not loser or not score:
            continue

        # strip seed/ranking markers like "#2", "DEF", "CH", "×2"
        def clean_name(n):
            n = re.sub(r"#\d+", "", n)
            n = re.sub(r"\b(DEF|CH)\b", "", n)
            n = re.sub(r"×\s*\d*", "", n)
            return " ".join(n.split())

        winner_c = clean_name(winner)
        loser_c = clean_name(loser)

        try:
            parsed_date = time.strptime(date_txt.replace("*", "").strip(), "%b %d, %Y")
            iso_date = time.strftime("%Y-%m-%d", parsed_date)
        except ValueError:
            continue

        tournament_link = cells[0].find("a")
        tournament = ""  # not present per-row on this page; filled by caller if needed

        gender_char = "m" if gender == "M" else "f"
        winner_slug = winner_c.replace(" ", "-").lower()
        loser_slug = loser_c.replace(" ", "-").lower()
        round_slug = current_round.lower()

        match_id = f"{iso_date[:4]}_{gender_char}_{iso_date}_{round_slug}_{winner_slug}_{loser_slug}"

        matches.append({
            "match_id": match_id,
            "date": iso_date,
            "tournament": tournament,
            "surface": "",
            "round": current_round,
            "player1": winner_c,
            "player2": loser_c,
            "winner": winner_c,
            "loser": loser_c,
            "score": score,
            "gender": gender,
            "best_of": 0,
            "draw_size": 0,
            "minutes": 0,
            "tourney_level": "",
            "tourney_id": "",
            "w_ace": 0, "w_df": 0, "w_svpt": 0, "w_1stIn": 0, "w_1stWon": 0,
            "w_2ndWon": 0, "w_SvGms": 0, "w_bpSaved": 0, "w_bpFaced": 0,
            "l_ace": 0, "l_df": 0, "l_svpt": 0, "l_1stIn": 0, "l_1stWon": 0,
            "l_2ndWon": 0, "l_SvGms": 0, "l_bpSaved": 0, "l_bpFaced": 0,
        })

    return matches


def fetch_season(tour, season, max_pages=20):
    all_matches = []
    for page in range(1, max_pages + 1):
        print(f"Fetching {tour} {season} page {page}...")
        html = fetch_page(tour, season, page)
        if not html:
            print("  FAILED, stopping")
            break
        rows = parse_rows(html, tour)
        print(f"  -> {len(rows)} matches parsed")
        if not rows:
            break
        all_matches.extend(rows)
        time.sleep(1)
    return all_matches


def load_existing(year):
    path = f"{BASE}/{year}.json"
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("matches", [])
    except (json.JSONDecodeError, OSError):
        return []


def dedupe_key(m):
    return (m.get("date"), m.get("winner", "").lower(), m.get("loser", "").lower())


def save(year, new_matches):
    existing = load_existing(year)
    seen = {dedupe_key(m) for m in existing}

    added = 0
    for m in new_matches:
        k = dedupe_key(m)
        if k not in seen:
            existing.append(m)
            seen.add(k)
            added += 1

    os.makedirs(BASE, exist_ok=True)
    path = f"{BASE}/{year}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"matches": existing}, f, indent=2, ensure_ascii=False)
    print(f"Saved {path} ({len(existing)} total matches, {added} newly added)")


def build_season(year):
    print(f"\n=== Building {year} ===")
    all_matches = []
    for gender in ("M", "F"):
        matches = fetch_season(gender, year)
        all_matches.extend(matches)
    if all_matches:
        save(year, all_matches)
    else:
        print(f"No matches parsed for {year} — see log above for why.")


def main():
    build_season(CURRENT_YEAR)
    build_season(PREV_YEAR)


if __name__ == "__main__":
    main()
