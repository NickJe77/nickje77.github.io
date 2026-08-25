"""
Howstat Test Match Scraper
=============================
Built against real Howstat page structure (verified via a diagnostic dump
of an actual match-list page and an actual scorecard page -- not guessed).

Source:
  List page:  https://www.howstat.com/Cricket/Statistics/Matches/MatchList.asp?Group={year}0101{year}1231&Range={year}
  Scorecard:  https://www.howstat.com/Cricket/Statistics/Matches/MatchScorecard.asp?MatchCode={code}

Key structural facts this was built against (from the real page dump):
  - The list page has several duplicate/nested tables; the one to actually
    use has class="TableLined". Row 0 is the header, each subsequent row
    is one match with 7 cells: [#, Date, Series, Test#-in-series, Ground,
    Result, "Test #NNNN"]. The scorecard link is the 3rd <a> in the row.
  - The Series cell looks like "2025-2026 Australia v. England" -- a
    leading year (or year range) followed by "TeamA v. TeamB".
  - The scorecard page has a table class="ScorecardMain" containing every
    innings concatenated together, separated by single-cell rows like
    "England 1st Innings". Within each innings: a BATTING header row,
    one row per batter (name, dismissal, R, BF, 4s, 6s, SR, %), then
    Extras/Total/Fall of Wickets rows.
  - Bowling figures are NOT reliably parsed from ScorecardMain (it also
    contains a messy duplicated blob row) -- instead there are separate
    clean table class="ScorecardBowling" elements, one per innings, in
    the same order the innings appear on the page.
  - A plain unclassed table whose first row's text is exactly
    "MATCH INFORMATION" holds Venue/Toss/Series/Match No./etc as
    label+value row pairs.
  - Player names in the batting table have '*' appended for captain and
    '†' appended for wicketkeeper, directly on the name with no space.
  - The Fall of Wickets cell contains a literal 'nbsp;' text artifact
    between some entries (Howstat's own markup quirk) that needs
    stripping before parsing.

Install:
  pip install undetected-chromedriver beautifulsoup4 setuptools

Run:
  python3 scrape_test_cricket.py 2026
  python3 scrape_test_cricket.py --year 2026
"""

import argparse
import json
import os
import random
import re
import time

import undetected_chromedriver as uc
from bs4 import BeautifulSoup, Comment

# ── Config ───────────────────────────────────────────────────────────

HOWSTAT_MATCHES_BASE = "https://www.howstat.com/Cricket/Statistics/Matches"
DATA_DIR              = "docs/data/test_cricket"
MIN_SLEEP              = 6
MAX_SLEEP              = 10

os.makedirs(DATA_DIR, exist_ok=True)

# ── Driver (headless -- GitHub Actions has no display server) ──────────

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
    # No version_main pin -- let undetected_chromedriver auto-detect
    # whatever Chrome version is actually installed on the runner.
    driver = uc.Chrome(use_subprocess=True, options=options)
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
    url = (
        f"{HOWSTAT_MATCHES_BASE}/MatchList.asp"
        f"?Group={year}0101{year}1231&Range={year}"
    )
    soup = get_soup(url)

    title = clean_text(soup.title.get_text()) if soup.title else "(no title)"
    print(f"  Page title: {title!r}")

    table = None
    for t in get_all_tables(soup):
        if "TableLined" in (t.get("class") or []):
            table = t
            break

    if table is None:
        print("  Could not find the TableLined match table on this page.")
        return []

    matches = []
    rows = table.find_all("tr")
    for row in rows[1:]:  # row 0 is the header
        cells = row.find_all("td")
        if len(cells) < 7:
            continue

        texts = [clean_text(c.get_text()) for c in cells]
        date        = texts[1]
        series_cell = texts[2]
        ground      = texts[4]
        result      = texts[5]
        test_no_txt = texts[6]  # "Test #2616"

        # "2025-2026 Australia v. England" -> strip leading year(s), split on " v. "
        m = re.match(r"^\s*\d{4}(?:-\d{4})?\s+(.+?)\s+v\.\s+(.+)$", series_cell)
        if m:
            team1, team2 = m.group(1).strip(), m.group(2).strip()
        else:
            # Fallback if the year-prefix pattern doesn't match for some
            # older/differently-formatted row -- just split on " v. " raw.
            parts = series_cell.split(" v. ")
            team1 = parts[0].strip() if parts else ""
            team2 = parts[1].strip() if len(parts) > 1 else ""

        links = [a.get("href") for a in row.find_all("a", href=True)]
        scorecard_href = next((l for l in links if l and "MatchScorecard.asp" in l), None)
        scorecard_url = f"{HOWSTAT_MATCHES_BASE}/{scorecard_href}" if scorecard_href else None

        match_number = to_int(test_no_txt)

        if not team1 or not team2:
            continue

        matches.append({
            "team1": team1,
            "team2": team2,
            "date": date,
            "ground": ground,
            "result": result,
            "match_number": match_number,
            "scorecard_url": scorecard_url,
        })

    print(f"  Found {len(matches)} Test(es) for {year}")
    return matches

# ── Full scorecard parsing ──────────────────────────────────────────────

def extract_match_number(text):
    m = re.search(r"Test\s*No\.?\s*#?\s*(\d+)|#\s*(\d+)", text, re.I)
    if m:
        for g in m.groups():
            if g:
                return int(g)
    return None


def parse_match_info_table(tables):
    """Finds the plain table whose first row is exactly 'MATCH INFORMATION'
    and reads the following label/value row pairs."""
    info = {}
    for t in tables:
        rows = t.find_all("tr")
        if not rows:
            continue
        first_text = clean_text(rows[0].get_text())
        if first_text != "MATCH INFORMATION":
            continue
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) != 2:
                continue
            key = clean_text(cells[0].get_text())
            val = clean_text(cells[1].get_text())
            if key:
                info[key] = val
        break

    # Normalize a couple of keys to match the naming already used
    # throughout the existing tests_2026.json data.
    if "Player of the Match" in info:
        info["Player of Match"] = info.pop("Player of the Match")
    info.setdefault("Match Type", "Test Match")
    return info


def parse_scorecard_main(main_table):
    """Parses the ScorecardMain table into a list of innings dicts
    (without bowling -- that comes from the separate ScorecardBowling
    tables, added in afterward)."""
    innings = []
    current = None

    for row in main_table.find_all("tr"):
        cells = row.find_all("td")
        texts = [clean_text(c.get_text()) for c in cells]
        if not texts:
            continue

        # Innings-label row: exactly one cell, ending in "Innings"
        # (optionally with a "(target N)" suffix for a run chase).
        if len(cells) == 1 and re.search(r"Innings(?:\s*\(target\s*\d+\))?\s*$", texts[0], re.I):
            if current:
                innings.append(current)
            team_m = re.match(r"^(.*?)\s+(?:1st|2nd|3rd|4th)\s+Innings", texts[0], re.I)
            current = {
                "team": team_m.group(1).strip() if team_m else texts[0],
                "total": None,
                "wickets": None,
                "overs": None,
                "run_rate": None,
                "batting": [],
                "extras": {"description": "", "runs": 0},
                "did_not_bat": [],
                "fall_of_wickets": [],
                "bowling": [],
            }
            continue

        if current is None:
            continue

        label0 = texts[0].strip().lower()

        if label0 in ("batting", "bowling"):
            continue

        if label0 == "extras":
            if len(texts) > 2:
                current["extras"]["description"] = texts[1]
                current["extras"]["runs"] = to_int(texts[2]) or 0
            continue

        if label0 == "total":
            if len(texts) > 2:
                current["total"] = to_int(texts[2])
                detail = texts[1]
                ov_m = re.search(r"([\d.]+)\s*overs", detail, re.I)
                rr_m = re.search(r"@\s*([\d.]+)\s*rpo", detail, re.I)
                wk_m = re.search(r"(\d+)\s*wickets?", detail, re.I)
                current["overs"] = to_float(ov_m.group(1)) if ov_m else None
                current["run_rate"] = to_float(rr_m.group(1)) if rr_m else None
                current["wickets"] = to_int(wk_m.group(1)) if wk_m else None
            continue

        if label0 == "fall of wickets":
            if len(texts) > 1:
                fow_text = texts[1].replace("nbsp;", " ")
                for m in re.finditer(r"(\d+)-(\d+)\s+([^,]+)", fow_text):
                    current["fall_of_wickets"].append({
                        "wicket": to_int(m.group(1)),
                        "runs": to_int(m.group(2)),
                        "batsman": clean_text(m.group(3)),
                    })
            continue

        if "did not bat" in label0:
            names_part = texts[1] if len(texts) > 1 else ""
            current["did_not_bat"] = [clean_text(n) for n in names_part.split(",") if clean_text(n)]
            continue

        # Regular batting row: name, dismissal, R, BF, 4s, 6s, SR[, %]
        if len(cells) >= 7:
            raw_name = texts[0]
            is_captain = raw_name.rstrip().endswith("*")
            is_keeper = "†" in raw_name
            name = raw_name.rstrip("*").replace("†", "").strip()
            current["batting"].append({
                "batsman": name,
                "is_captain": is_captain,
                "is_keeper": is_keeper,
                "dismissal": texts[1],
                "runs": to_int(texts[2]),
                "balls_faced": to_int(texts[3]),
                "fours": to_int(texts[4]),
                "sixes": to_int(texts[5]),
                "strike_rate": to_float(texts[6]),
            })

    if current:
        innings.append(current)

    return innings


def parse_bowling_tables(tables, innings):
    """ScorecardBowling tables appear in the same order as the innings on
    the page, one each. Attaches bowling figures to the matching innings
    by position rather than by team name (safer -- team names could in
    theory collide with substring matches, position can't)."""
    bowling_tables = [t for t in tables if "ScorecardBowling" in (t.get("class") or [])]
    for i, bt in enumerate(bowling_tables):
        if i >= len(innings):
            break
        bowlers = []
        rows = bt.find_all("tr")
        for row in rows[1:]:  # skip header row
            cells = row.find_all("td")
            if len(cells) < 6:
                continue
            texts = [clean_text(c.get_text()) for c in cells]
            bowlers.append({
                "bowler": texts[0],
                "overs": to_float(texts[1]),
                "maidens": to_int(texts[2]),
                "runs": to_int(texts[3]),
                "wickets": to_int(texts[4]),
                "economy": to_float(texts[5]),
            })
        innings[i]["bowling"] = bowlers


def parse_scorecard(soup, match_meta):
    tables = get_all_tables(soup)

    title_tag = soup.find("title")
    title = clean_text(title_tag.get_text()) if title_tag else ""

    match_number = extract_match_number(title) or match_meta.get("match_number")

    match_info = parse_match_info_table(tables)

    main_table = None
    for t in tables:
        if "ScorecardMain" in (t.get("class") or []):
            main_table = t
            break

    innings = []
    if main_table is not None:
        innings = parse_scorecard_main(main_table)
        parse_bowling_tables(tables, innings)
    else:
        print("  Could not find ScorecardMain table on this page.")

    return {
        "match_type": "Test",
        "match_number": match_number,
        "url": match_meta.get("scorecard_url") or "",
        "title": title,
        "match_info": match_info,
        "innings": innings,
    }, match_number

# ── Build one year ───────────────────────────────────────────────────

def build_year(year):
    print(f"\n📅 BUILDING {year}")

    year_matches = get_year_matches(year)
    if not year_matches:
        print("❌ no matches found -- check the list-page URL / TableLined structure")
        return

    results = []

    for i, m in enumerate(year_matches, 1):
        print(f"\n  [{i}/{len(year_matches)}] {m['team1']} v {m['team2']} — {m['date']}")

        if not m["scorecard_url"]:
            print("    -> no scorecard link, skipping")
            continue

        soup = get_soup(m["scorecard_url"])
        scorecard, match_number = parse_scorecard(soup, m)

        results.append({
            "year": str(year),
            "date": m["date"],
            "teams": f"{m['team1']} v {m['team2']}",
            "ground": m["ground"],
            "result": m["result"],
            "match_number": match_number,
            "scorecard": scorecard,
        })

        n_innings = len(scorecard["innings"])
        n_bat = sum(len(inn["batting"]) for inn in scorecard["innings"])
        n_bowl = sum(len(inn["bowling"]) for inn in scorecard["innings"])
        print(f"    -> {n_innings} innings, {n_bat} batting entries, "
              f"{n_bowl} bowling entries, match_number={match_number}")

        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))

    out_path = f"{DATA_DIR}/tests_{year}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"year": str(year), "matches": results}, f, indent=2, ensure_ascii=False)

    print(f"\n✅ saved {len(results)} match(es) -> {out_path}")

# ── Main ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int, nargs="?", help="Year to scrape, e.g. 2026")
    ap.add_argument("--year", dest="year_flag", type=int, help="Same as the positional year argument")
    args = ap.parse_args()
    if args.year_flag is not None:
        args.year = args.year_flag
    if args.year is None:
        ap.error("year is required, e.g. 'python3 scrape_test_cricket.py 2026' or '--year 2026'")

    build_year(args.year)

    try:
        DRIVER.quit()
    except Exception:
        pass

    print("\nDONE")


if __name__ == "__main__":
    main()
