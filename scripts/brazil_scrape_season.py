#!/usr/bin/env python3
"""
brazil_scrape_season.py

Discovers every match in a Brazilian Serie A season on worldfootball.net
and scrapes each one's full report (score, events, lineups) using the
already-verified match report parser.

REQUIRES SETUP BEFORE FIRST RUN:
COMPETITION_PATH below is a PLACEHOLDER, not a verified value. The
J-League version of this script used "competition/co48/japan-j1-league"
-- that "co48" is an internal worldfootball.net ID specific to J1
League, and there's no way to derive Brazilian Serie A's own ID from
its name. I don't have network access to worldfootball.net to look
this up myself. Go to worldfootball.net, find the Brazilian Serie A
competition page, and copy the path from its URL (it'll look like
"competition/coXX/brasileirao-serie-a" or similar) into COMPETITION_PATH
below before running this.

KNOWN UNCERTAINTY (read before trusting old seasons):
The J-League version of this script found (via a real saved match
page) that early J-League seasons were split into "stages" requiring
special handling. I have NO equivalent verified evidence for Brazilian
Serie A -- Brazil's league has gone through its own different format
changes over the decades (round-robin eras, groups-plus-playoffs eras),
which may or may not surface as a similar "stage" pattern on
worldfootball.net specifically. Don't assume either way. The season
discovery logic below still tries the season-navigation dropdown first
(the same defensive approach as the J-League version) and prints a
warning rather than silently writing an empty file if nothing is
found for a given year, so a genuine problem stays visible instead of
being swallowed -- but the exact shape of any old-season quirks here
is unverified until checked against real pages.

Writes, per season, in the SAME schema build scripts elsewhere in this
repo already expect (adapt paths below to match your actual repo
layout before wiring into a workflow):

  docs/data/brazilseriea/seasons/{year}.json
      { "season": year, "source": url, "updated": iso timestamp,
        "games": [ {game_id, date, home_team, away_team,
                     home_score, away_score, match_url}, ... ] }

  docs/data/brazilseriea/matches/{year}/{game_id}.json
      full parsed match report (score/events/facts/lineups)

Usage:
    python3 brazil_scrape_season.py 2025
"""

import json
import os
import re
import sys
import time
import datetime as dt

import requests
from bs4 import BeautifulSoup

# Import the already-tested match report parser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brazil_match_scraper import parse_match_report, team_id_from_href

BASE = "https://www.worldfootball.net"

COMPETITION_PATH = "competition/co112/brazil-serie-a"

OUT_ROOT = "docs/data/brazilseriea"
SEASONS_DIR = f"{OUT_ROOT}/seasons"
MATCHES_DIR = f"{OUT_ROOT}/matches"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch(url, retries=4):
    for i in range(retries):
        try:
            res = session.get(url, timeout=30)
            if res.status_code == 200:
                return res.text
            if res.status_code == 404:
                print(f"  HTTP 404 (not found) for {url}")
                return None
            print(f"  HTTP {res.status_code} for {url}, retrying...")
        except requests.RequestException as e:
            print(f"  request error: {e}, retrying...")
        time.sleep(4)
    return None


def discover_season_id_map():
    """
    Fetch the season-navigation dropdown (present on any /all-matches/
    page) and build a {label: all_matches_url} map. This mechanism is
    the same one verified working for J-League, and worldfootball.net
    uses the same dropdown template across its competitions, so it
    should work the same way here -- but the SPECIFIC label patterns
    below are what J-League's dropdown actually contained, not
    something confirmed for Brazilian Serie A:

        "2025"            -> single-stage season       (J-League example)
        "2004 Playoff"    -> separate championship, not the season
        "2003 1st stage"  -> first half of a split season
        "2003 2nd stage"  -> second half of a split season

    Brazilian Serie A may use different label wording entirely (its
    own history includes round-robin eras and groups-plus-playoffs
    eras that don't necessarily map onto J-League's "1st/2nd stage"
    split). resolve_year_urls() below only checks for the word
    "playoff" (case-insensitive) to exclude non-season entries -- if
    Brazil's dropdown uses different wording for its championship/
    playoff entries, that filter will need adjusting once you can see
    the real dropdown contents. Print season_map.keys() on a first run
    to check this before trusting the output.
    """
    url = f"{BASE}/{COMPETITION_PATH}/all-matches/"
    print(f"Fetching season list: {url}")
    html = fetch(url)
    if not html:
        print("  FAILED to fetch season navigation page")
        return {}

    soup = BeautifulSoup(html, "html.parser")
    select = soup.select_one("select.season-navigation")
    if not select:
        print("  WARNING: no season-navigation dropdown found on this page")
        return {}

    season_map = {}
    for opt in select.find_all("option"):
        label = opt.get_text(strip=True)
        href = opt.get("value", "")
        if not href:
            continue
        full_url = BASE + href if href.startswith("/") else href
        season_map[label] = full_url

    print(f"  found {len(season_map)} season/stage entries in dropdown")
    return season_map


def resolve_year_urls(season_map, year):
    """
    Given the raw {label: url} map, return the list of all-matches
    URLs that together make up a given year's REGULAR SEASON - i.e.
    excluding "Playoff" entries, but including both stages for years
    that had a 1st/2nd stage split.
    """
    year_str = str(year)
    urls = []
    for label, url in season_map.items():
        if not label.startswith(year_str):
            continue
        if "playoff" in label.lower():
            continue  # championship final, not part of the season proper
        urls.append((label, url))
    # stable order: plain year label first, then "1st stage" before "2nd stage"
    urls.sort(key=lambda t: (("1st" not in t[0]), t[0]))
    return urls


def discover_season_matches(year, known_urls=None):
    """
    Returns list of {game_id, date, home_team, away_team, home_score,
    away_score, match_url} or [] if nothing found.

    known_urls: list of (label, url) tuples - the confirmed all-matches
    URL(s) for this year from resolve_year_urls(). For split-season
    years this is 2 URLs (1st stage + 2nd stage); combine into one
    games list. Falls back to unverified plain-year guesses only if
    no known_urls available.
    """
    candidate_urls = [u for _, u in known_urls] if known_urls else [
        f"{BASE}/{COMPETITION_PATH}/{year}-{year+1}/all-matches/",
        f"{BASE}/{COMPETITION_PATH}/{year}/all-matches/",
    ]

    all_games = []
    used_urls = []

    for url in candidate_urls:
        html = fetch(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("[data-match_id]")
        if not rows:
            debug_dir = "debug_html"
            os.makedirs(debug_dir, exist_ok=True)
            safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", url)[:120]
            debug_path = f"{debug_dir}/{safe_name}.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  fetched {url} (200 OK) but found 0 rows with [data-match_id] "
                  f"- saved raw response to {debug_path} for inspection")
            continue

        print(f"  fetched {url} (200 OK), found {len(rows)} rows with [data-match_id]")

        games = []
        current_date = None
        skipped_rows = []

        for row in rows:
            sib = row
            while sib is not None:
                sib = sib.find_previous_sibling()
                if sib is None:
                    break
                sib_classes = sib.get("class", []) if hasattr(sib, "get") else []
                if "date-head" in sib_classes:
                    current_date = sib.get_text(strip=True)
                    break
                if sib.get("data-match_id"):
                    break

            match_id = row.get("data-match_id")
            home_el = row.select_one(".team-name-home") or row.select_one(".team-shortname-home")
            away_el = row.select_one(".team-name-away") or row.select_one(".team-shortname-away")
            result_link = row.select_one(".match-result a")

            if not (match_id and home_el and away_el and result_link):
                skipped_rows.append((match_id, bool(home_el), bool(away_el), bool(result_link)))
                continue

            score_text = result_link.get_text(strip=True)
            score_m = re.match(r"(\d+):(\d+)", score_text)

            games.append({
                "game_id": match_id,
                "date": current_date,
                "home_team": home_el.get_text(strip=True),
                "away_team": away_el.get_text(strip=True),
                "home_score": int(score_m.group(1)) if score_m else None,
                "away_score": int(score_m.group(2)) if score_m else None,
                "match_url": BASE + result_link["href"] if result_link.get("href", "").startswith("/") else result_link.get("href"),
            })

        if games:
            all_games.extend(games)
            used_urls.append(url)
        elif skipped_rows:
            print(f"  found {len(rows)} rows but extracted 0 games - "
                  f"(match_id, has_home, has_away, has_result_link) for first 3 skipped rows: "
                  f"{skipped_rows[:3]}")
            debug_dir = "debug_html"
            os.makedirs(debug_dir, exist_ok=True)
            safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", url)[:120]
            debug_path = f"{debug_dir}/{safe_name}.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  saved raw response to {debug_path} for inspection")

    if not all_games:
        print(f"  WARNING: no matches discovered for {year} across any known URL.")

    return all_games, "; ".join(used_urls) if used_urls else None


def scrape_season(year, skip_existing=True, known_urls=None):
    os.makedirs(SEASONS_DIR, exist_ok=True)
    match_dir = f"{MATCHES_DIR}/{year}"
    os.makedirs(match_dir, exist_ok=True)

    print(f"Discovering fixtures for {year}...")
    games, source_url = discover_season_matches(year, known_urls=known_urls)
    print(f"  found {len(games)} candidate matches")

    season_out = {
        "season": year,
        "source": source_url,
        "updated": dt.datetime.utcnow().isoformat() + "Z",
        "games": [{k: v for k, v in g.items() if k != "match_url"} for g in games],
    }
    with open(f"{SEASONS_DIR}/{year}.json", "w", encoding="utf-8") as f:
        json.dump(season_out, f, indent=2, ensure_ascii=False)
    print(f"  wrote {SEASONS_DIR}/{year}.json")

    fetched, skipped, failed = 0, 0, 0
    for g in games:
        out_path = f"{match_dir}/{g['game_id']}.json"
        if skip_existing and os.path.exists(out_path):
            skipped += 1
            continue

        print(f"  fetching match {g['game_id']}: {g['home_team']} vs {g['away_team']}")
        html = fetch(g["match_url"])
        if not html:
            print(f"    FAILED to fetch {g['match_url']}")
            failed += 1
            continue

        try:
            data = parse_match_report(html)
        except Exception as e:
            print(f"    FAILED to parse: {e}")
            failed += 1
            continue

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        fetched += 1
        time.sleep(2)  # be polite to the source site

    print(f"Done {year}: fetched={fetched} skipped(existing)={skipped} failed={failed} "
          f"of {len(games)} discovered")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 brazil_scrape_season.py <year>   # one season (all its stages)")
        print("  python3 brazil_scrape_season.py all      # every season, oldest to newest")
        sys.exit(1)

    arg = sys.argv[1]

    season_map = discover_season_id_map()
    if not season_map:
        print("Could not build season list - aborting rather than guessing URLs.")
        sys.exit(1)

    # every distinct year that appears in the dropdown, oldest first
    years = sorted({
        int(m.group(1)) for label in season_map
        for m in [re.match(r"(\d{4})", label)] if m
    })

    if arg == "all":
        for year in years:
            urls = resolve_year_urls(season_map, year)
            if not urls:
                print(f"  WARNING: {year} has no non-playoff entries in the dropdown - skipping")
                continue
            scrape_season(year, known_urls=urls)
            time.sleep(3)
    else:
        year = int(arg)
        urls = resolve_year_urls(season_map, year)
        if not urls:
            print(f"  WARNING: {year} not found in season dropdown - falling back to "
                  f"unverified plain-year URL guesses for this season only.")
        else:
            print(f"  resolved {year} to {len(urls)} stage URL(s): {[l for l, _ in urls]}")
        scrape_season(year, known_urls=urls)


if __name__ == "__main__":
    main()
