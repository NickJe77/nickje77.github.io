#!/usr/bin/env python3

"""
scrape_epl_season.py

Scrapes the current Premier League season's fixtures and results from
fbref.com and writes them to docs/data/epl/seasons/<season>.json in the
exact schema the site's existing season files already use:

    {
      "season": "2026-2027",
      "games": [
        {
          "match_id": "2026-2027_0001",
          "date": "2026-08-15",
          "home": "Liverpool",
          "away": "Bournemouth",
          "score_home": 4,
          "score_away": 2,
          "venue": "Anfield",
          "match_report_url": "https://fbref.com/en/matches/..."
        },
        ...
      ]
    }

Fixtures that haven't been played yet are still included, with
score_home/score_away set to null - re-running this script later in the
season picks up newly completed results automatically, since fbref's
schedule page always reflects the season's current state.

IMPORTANT: this needs to run somewhere with real internet access to
fbref.com. It will NOT work inside a sandboxed environment without
outbound access to that domain - run it locally, or via a GitHub Action
(see scrape-epl.yml).

Place this file in the scripts/ folder.
Run from the root of your GitHub repo (nickje77.github.io/):

    python3 scripts/scrape_epl_season.py [season]

If no season is given, it defaults to the current Premier League season
based on today's date (August-July season boundary).
"""

import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Comment

REPO_ROOT = Path(__file__).parent.parent
OUT_DIR = REPO_ROOT / "docs" / "data" / "epl" / "seasons"

FBREF_COMP_ID = 9  # Premier League's competition id on fbref
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def current_season() -> str:
    """Premier League seasons run August to May. If today is before
    August, we're still in the season that started last calendar year."""
    today = date.today()
    start_year = today.year if today.month >= 7 else today.year - 1
    return f"{start_year}-{start_year + 1}"


def fetch_schedule_html(season: str) -> str:
    url = (
        f"https://fbref.com/en/comps/{FBREF_COMP_ID}/{season}/schedule/"
        f"{season}-Premier-League-Scores-and-Fixtures"
    )
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def find_schedule_table(soup: BeautifulSoup):
    """fbref sometimes wraps tables inside HTML comments to defeat naive
    scrapers - check both the live DOM and any commented-out blocks."""
    table = soup.find("table", id=re.compile(r"^sched_"))
    if table:
        return table

    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if "sched_" in comment:
            inner = BeautifulSoup(comment, "lxml")
            table = inner.find("table", id=re.compile(r"^sched_"))
            if table:
                return table

    return None


def parse_score(raw: str):
    """fbref renders played-match scores as e.g. '4–2' (en dash). Upcoming
    fixtures have an empty score cell."""
    raw = (raw or "").strip()
    if not raw:
        return None, None
    # fbref uses an en dash (\u2013), not a hyphen
    parts = re.split(r"[\u2013\-]", raw)
    if len(parts) != 2:
        return None, None
    try:
        return int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        return None, None


def parse_games(table, season: str) -> list:
    games = []
    rows = table.find("tbody").find_all("tr")

    for row in rows:
        # Header/spacer rows inside the body have class "thead" - skip them
        if "thead" in (row.get("class") or []):
            continue

        cells = {c.get("data-stat"): c for c in row.find_all(["th", "td"])}
        if not cells or "date" not in cells:
            continue

        date_cell = cells.get("date")
        date_str = date_cell.get("csk") or (date_cell.get_text(strip=True) if date_cell else "")
        if not date_str:
            continue
        # csk attribute is already YYYY-MM-DD when present; fall back to
        # parsing the visible text if it's missing
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            continue

        home = cells.get("home_team")
        away = cells.get("away_team")
        score_cell = cells.get("score")
        venue = cells.get("venue")
        report_cell = cells.get("match_report")

        home_name = home.get_text(strip=True) if home else ""
        away_name = away.get_text(strip=True) if away else ""
        if not home_name or not away_name:
            continue

        score_home, score_away = parse_score(score_cell.get_text(strip=True) if score_cell else "")

        report_link = report_cell.find("a") if report_cell else None
        report_url = None
        if report_link and report_link.get("href"):
            href = report_link["href"]
            report_url = href if href.startswith("http") else f"https://fbref.com{href}"

        games.append({
            "date": date_str,
            "home": home_name,
            "away": away_name,
            "score_home": score_home,
            "score_away": score_away,
            "venue": venue.get_text(strip=True) if venue else "",
            "match_report_url": report_url,
        })

    # Sort by date (then by original order for same-day fixtures) before
    # assigning sequential match_ids, matching the existing file convention
    games.sort(key=lambda g: g["date"])
    for i, g in enumerate(games, start=1):
        g_with_id = {"match_id": f"{season}_{i:04d}"}
        g_with_id.update(g)
        games[i - 1] = g_with_id

    return games


def main():
    season = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else current_season()
    print(f"Fetching {season} Premier League schedule from fbref...")

    html = fetch_schedule_html(season)
    soup = BeautifulSoup(html, "lxml")

    table = find_schedule_table(soup)
    if table is None:
        print("ERROR: could not find the schedule table on the page.", file=sys.stderr)
        print("fbref may have changed their page structure - check the", file=sys.stderr)
        print("table id (expected something starting with 'sched_') by hand.", file=sys.stderr)
        sys.exit(1)

    games = parse_games(table, season)
    if not games:
        print("ERROR: schedule table found but zero games parsed.", file=sys.stderr)
        print("fbref may have changed their column data-stat names - check", file=sys.stderr)
        print("them against a saved copy of the page.", file=sys.stderr)
        sys.exit(1)

    played = sum(1 for g in games if g["score_home"] is not None)
    print(f"Parsed {len(games)} fixtures ({played} played, {len(games) - played} upcoming).")

    output = {"season": season, "games": games}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{season}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
