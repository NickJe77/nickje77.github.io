"""
Cricinfo Test Match Scraper
=============================
Uses undetected_chromedriver — same approach as the World Cup scrapers in
this project (world_cup_mens_scraper.py / scrape_worldcup_2026.py).

Source: ESPN Cricinfo's Statsguru "team match results" index
(class=1 is Cricinfo's long-standing code for Test matches, as opposed
to class=2 for ODIs and class=3 for T20Is), plus each match's full
scorecard page.

Note: match_number extraction was dropped -- the regex that pulled a
"Test #" from the scorecard page was matching the wrong number on every
match (it returned "18" across the board, and misfired onto the date
field on some pages), so it's been removed rather than shipped broken.
Re-add it later once there's a real scorecard page to check the actual
Test-number markup against.

FIRST-DRAFT WARNING: unlike the football scrapers in this project, this
was built without being able to load a single real Cricinfo page (no
network access to espncricinfo.com from the environment this was written
in). The year-index URL and Test-numbering convention are Cricinfo
patterns I'm confident are real, but the exact CSS/data-stat selectors
on the full-scorecard page are inferred, not verified. Expect to run
this against one real match, compare the printed field values to that
match's actual scorecard, and fix selector mismatches — the same way
scrape_worldcup_2026.py needed a URL fix before it worked.

Install:
  pip install undetected-chromedriver beautifulsoup4 setuptools

Run:
  python3 scrape_test_cricket.py --year 2026

Chrome/ChromeDriver version note:
  make_driver() reads a CHROME_VERSION env var (major.minor.build.patch,
  e.g. "151.0.7922.137") and pins undetected_chromedriver's version_main
  to its major version. In CI this is set from the browser-actions/
  setup-chrome step's output, so the driver undetected_chromedriver
  downloads always matches whatever Chrome build actually got installed
  that run -- letting uc auto-detect on its own can grab a ChromeDriver
  built for a slightly newer Chrome than what's on the runner, which
  raises selenium.common.exceptions.SessionNotCreatedException. If
  CHROME_VERSION isn't set (e.g. running locally), it falls back to
  uc's normal auto-detection.
"""

import argparse
import json
import os
import random
import re
import shutil
import time
from pathlib import Path

import undetected_chromedriver as uc
from bs4 import BeautifulSoup, Comment

# ── Config ───────────────────────────────────────────────────────────

BASE          = "https://www.espncricinfo.com"
STATS_BASE    = "https://stats.espncricinfo.com"
DATA_DIR      = "docs/data/test_cricket"
MIN_SLEEP     = 6
MAX_SLEEP     = 10

os.makedirs(DATA_DIR, exist_ok=True)

# ── Driver (same pattern as the football scrapers) ─────────────────────

def make_driver():
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-features=Translate")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Pin version_main to whatever Chrome the workflow actually installed
    # this run (passed in via CHROME_VERSION env var, set from
    # browser-actions/setup-chrome's output). uc's own auto-detection can
    # grab a ChromeDriver build slightly ahead of what "stable" resolves
    # to on the runner, which raises SessionNotCreatedException. Reading
    # the real installed version here keeps driver and browser in sync
    # without hardcoding a version number that would go stale.
    chrome_version = os.environ.get("CHROME_VERSION")
    version_main = int(chrome_version.split(".")[0]) if chrome_version else None

    driver = uc.Chrome(use_subprocess=True, options=options, version_main=version_main)
    driver.set_page_load_timeout(120)
    return driver


DRIVER = make_driver()


def get_html(url):
    global DRIVER
    while True:
        try:
            DRIVER.get(url)
            time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
            html = DRIVER.page_source
            if not html.strip():
                raise Exception("blank html")
            if "verify you are human" in html.lower() or "attention required" in html.lower():
                print("⚠️ BLOCKED — waiting 60s")
                time.sleep(60)
                continue
            return html
        except Exception as e:
            print("⚠️ DRIVER RESTART:", e)
            try:
                DRIVER.quit()
            except Exception:
                pass
            time.sleep(5)
            DRIVER = make_driver()


def get_soup(url):
    print(f"  GET {url}")
    return BeautifulSoup(get_html(url), "html.parser")


def get_all_tables(soup):
    """Same approach as the football scrapers: check visible tables AND
    tables hidden inside HTML comments (a common pattern on stats sites
    to dodge simple scrapers, seen already on fbref -- worth checking for
    on Cricinfo too even though I can't confirm it's actually used here)."""
    tables = []
    seen = set()
    for t in soup.find_all("table"):
        key = id(t)
        if key not in seen:
            seen.add(key)
            tables.append(t)
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        try:
            csoup = BeautifulSoup(comment, "html.parser")
        except Exception:
            continue
        for t in csoup.find_all("table"):
            tables.append(t)
    return tables

# ── Text helpers ─────────────────────────────────────────────────────

def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def to_int(text):
    if text is None:
        return None
    text = clean_text(str(text)).replace(",", "")
    m = re.search(r"-?\d+", text)
    return int(m.group(0)) if m else None


def to_float(text):
    if text is None:
        return None
    text = clean_text(str(text))
    m = re.search(r"-?\d+\.?\d*", text)
    return float(m.group(0)) if m else None

# ── Year index (list of matches + scorecard links) ─────────────────────

def get_year_matches(year):
    """Cricinfo Statsguru match-results index. class=1 = Test matches.
    This URL pattern (stats.espncricinfo.com/ci/engine/records/team/
    match_results.html) has existed on Cricinfo for a very long time and
    is the most stable entry point I know of for "every Test in year X"
    -- much more so than guessing at a modern frontend URL, which
    Cricinfo has redesigned multiple times."""

    url = (
        f"{STATS_BASE}/ci/engine/records/team/match_results.html"
        f"?class=1;id={year};type=year"
    )
    soup = get_soup(url)

    matches = []
    for table in get_all_tables(soup):
        if "engineTable" not in (table.get("class") or []):
            continue
        rows = table.find_all("tr", class_="data1")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 6:
                continue

            team1 = clean_text(cells[0].get_text())
            team2 = clean_text(cells[1].get_text())
            winner = clean_text(cells[2].get_text())
            margin = clean_text(cells[3].get_text())
            ground = clean_text(cells[4].get_text())
            date   = clean_text(cells[5].get_text())

            scorecard_link = row.find("a", href=True)
            scorecard_url = (
                BASE + scorecard_link["href"]
                if scorecard_link and scorecard_link["href"].startswith("/")
                else (scorecard_link["href"] if scorecard_link else None)
            )

            if not team1 or not team2:
                continue

            result = ""
            if winner and winner not in ("drawn", "no result", "tied", "-"):
                result = f"{winner} won {margin}" if margin else f"{winner} won"
            elif winner:
                result = winner.capitalize()

            matches.append({
                "team1": team1,
                "team2": team2,
                "date": date,
                "ground": ground,
                "result": result,
                "scorecard_url": scorecard_url,
            })

    print(f"  Found {len(matches)} Test(es) for {year}")
    return matches

# ── Full scorecard parsing ──────────────────────────────────────────────

def extract_match_info(soup):
    """Grabs the key/value strip Cricinfo shows above a scorecard
    (Toss, Series, Player of the Match, Match days, etc). This is
    guessed as a definition-list / label+value pair pattern -- the
    single most likely part of this script to need a selector fix
    against the real page."""
    info = {}

    for row in soup.select("[class*='match-info'] div, .match-information div"):
        label = row.find(class_=re.compile("label|title", re.I))
        value = row.find(class_=re.compile("value|content", re.I))
        if label and value:
            key = clean_text(label.get_text())
            val = clean_text(value.get_text())
            if key and val:
                info[key] = val

    # Fallback: look for plain "Label: Value" text lines in a summary block
    if not info:
        summary = soup.find(class_=re.compile("match-summary|series-summary", re.I))
        if summary:
            for line in summary.stripped_strings:
                m = re.match(r"^([A-Za-z .]+):\s*(.+)$", line)
                if m:
                    info[m.group(1).strip()] = m.group(2).strip()

    return info


def parse_innings_table(table):
    """Parses one Cricinfo batting table (one innings) into the
    batting/extras/did_not_bat/fall_of_wickets/bowling structure used
    throughout tests_2026.json."""

    batting = []
    extras = {"description": "", "runs": 0}
    did_not_bat = []
    total = None
    wickets = None
    overs = None
    run_rate = None

    rows = table.find_all("tr")

    for row in rows:
        cells = row.find_all("td")
        row_text = clean_text(row.get_text(" "))

        if not cells:
            continue

        # Extras row
        if row_text.lower().startswith("extras"):
            m = re.search(r"\((.*?)\)\s*(\d+)?", row_text)
            if m:
                extras["description"] = f"({m.group(1)}) {m.group(2) or ''}".strip()
                extras["runs"] = to_int(m.group(2)) or 0
            continue

        # Total row
        if row_text.lower().startswith("total"):
            total = to_int(row_text)
            ov_m = re.search(r"([\d.]+)\s*Overs", row_text, re.I)
            if ov_m:
                overs = to_float(ov_m.group(1))
            rr_m = re.search(r"RR:\s*([\d.]+)", row_text, re.I)
            if rr_m:
                run_rate = to_float(rr_m.group(1))
            wk_m = re.search(r"\((\d+)\s*wkts?\)", row_text, re.I)
            wickets = to_int(wk_m.group(1)) if wk_m else None
            continue

        # Did not bat row
        if "did not bat" in row_text.lower():
            names_part = row_text.split(":", 1)[-1] if ":" in row_text else row_text
            did_not_bat = [clean_text(n) for n in names_part.split(",") if clean_text(n)]
            continue

        # Regular batting row: expects name, dismissal, runs, balls, 4s, 6s, SR
        if len(cells) >= 6:
            name_cell = cells[0]
            name = clean_text(name_cell.get_text())
            if not name or name.lower() in ("batter", "batsman"):
                continue

            is_captain = "(c)" in name or "captain" in name_cell.get("class", [])
            is_keeper = "†" in name or "wk" in " ".join(name_cell.get("class", [])).lower()
            name = name.replace("(c)", "").replace("†", "").strip()

            dismissal = clean_text(cells[1].get_text()) if len(cells) > 1 else ""

            try:
                batting.append({
                    "batsman": name,
                    "is_captain": bool(is_captain),
                    "is_keeper": bool(is_keeper),
                    "dismissal": dismissal,
                    "runs": to_int(cells[2].get_text()) if len(cells) > 2 else None,
                    "balls_faced": to_int(cells[3].get_text()) if len(cells) > 3 else None,
                    "fours": to_int(cells[4].get_text()) if len(cells) > 4 else None,
                    "sixes": to_int(cells[5].get_text()) if len(cells) > 5 else None,
                    "strike_rate": to_float(cells[6].get_text()) if len(cells) > 6 else None,
                })
            except Exception:
                continue

    return {
        "total": total,
        "wickets": wickets,
        "overs": overs,
        "run_rate": run_rate,
        "batting": batting,
        "extras": extras,
        "did_not_bat": did_not_bat,
    }


def parse_bowling_table(table):
    bowling = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        name = clean_text(cells[0].get_text())
        if not name or name.lower() == "bowler":
            continue
        try:
            bowling.append({
                "bowler": name,
                "overs": to_float(cells[1].get_text()),
                "maidens": to_int(cells[2].get_text()),
                "runs": to_int(cells[3].get_text()),
                "wickets": to_int(cells[4].get_text()),
                "economy": to_float(cells[5].get_text()),
            })
        except Exception:
            continue
    return bowling


def parse_fall_of_wickets(soup, innings_index):
    """Cricinfo usually shows fall of wickets as a single text line like
    '1-35 (Duckett), 2-51 (Crawley), ...' near the relevant innings."""
    fow = []
    block = soup.find(string=re.compile(r"Fall of wickets", re.I))
    if not block:
        return fow
    container = block.find_parent()
    if not container:
        return fow
    text = clean_text(container.get_text(" "))
    for m in re.finditer(r"(\d+)-(\d+)\s*\(([^),]+)", text):
        fow.append({
            "wicket": to_int(m.group(1)),
            "runs": to_int(m.group(2)),
            "batsman": clean_text(m.group(3)),
        })
    return fow


def parse_scorecard(soup, match_meta):
    match_info = extract_match_info(soup)

    title_tag = soup.find("title")
    title = clean_text(title_tag.get_text()) if title_tag else ""

    innings = []

    # Cricinfo scorecards alternate a batting table then a bowling table
    # per innings. Grouping by proximity/order is inferred here -- if the
    # real page nests them differently (e.g. both tables inside one
    # innings container with an id like "innings-1"), that's the first
    # thing to check when debugging this against a live page.
    all_tables = get_all_tables(soup)
    batting_tables = [t for t in all_tables if t.find("th", string=re.compile("Runs|R$", re.I))]
    bowling_tables = [t for t in all_tables if t.find("th", string=re.compile("Overs|O$", re.I)) and t not in batting_tables]

    team_names = [match_meta["team1"], match_meta["team2"]]

    for i, bat_table in enumerate(batting_tables):
        inn = parse_innings_table(bat_table)
        inn["team"] = team_names[i % 2]
        inn["fall_of_wickets"] = parse_fall_of_wickets(soup, i)
        inn["bowling"] = parse_bowling_table(bowling_tables[i]) if i < len(bowling_tables) else []
        innings.append(inn)

    return {
        "match_type": "Test",
        "url": match_meta.get("scorecard_url") or "",
        "title": title,
        "match_info": match_info,
        "innings": innings,
    }

# ── Build one year ───────────────────────────────────────────────────

def build_year(year):
    print(f"\n📅 BUILDING {year}")

    year_matches = get_year_matches(year)
    if not year_matches:
        print("❌ no matches found -- check the Statsguru URL / page structure")
        return

    results = []

    for i, m in enumerate(year_matches, 1):
        print(f"\n  [{i}/{len(year_matches)}] {m['team1']} v {m['team2']} — {m['date']}")

        if not m["scorecard_url"]:
            print("    -> no scorecard link, skipping")
            continue

        soup = get_soup(m["scorecard_url"])

        # TEMP DEBUG: dump the raw HTML of the first real scorecard page
        # we fetch so the actual markup can be inspected (via the repo,
        # since this environment has no direct network access to
        # espncricinfo.com). This file is picked up automatically by the
        # existing `git add docs/data/test_cricket/` commit step.
        # Safe to delete this block and the debug file once the real
        # selectors in parse_scorecard/parse_innings_table/
        # extract_match_info have been fixed against real markup.
        if i == 1:
            debug_path = f"{DATA_DIR}/_debug_scorecard_sample.html"
            with open(debug_path, "w", encoding="utf-8") as dbg:
                dbg.write(soup.prettify())
            print(f"    -> wrote debug HTML sample to {debug_path}")

        scorecard = parse_scorecard(soup, m)

        results.append({
            "year": str(year),
            "date": m["date"],
            "teams": f"{m['team1']} v {m['team2']}",
            "ground": m["ground"],
            "result": m["result"],
            "scorecard": scorecard,
        })

        n_innings = len(scorecard["innings"])
        n_bat = sum(len(inn["batting"]) for inn in scorecard["innings"])
        print(f"    -> {n_innings} innings parsed, {n_bat} batting entries")

        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))

    out_path = f"{DATA_DIR}/tests_{year}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"year": str(year), "matches": results}, f, indent=2, ensure_ascii=False)

    print(f"\n✅ saved {len(results)} match(es) -> {out_path}")

# ── Main ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()

    build_year(args.year)

    try:
        DRIVER.quit()
    except Exception:
        pass

    print("\nDONE")


if __name__ == "__main__":
    main()
