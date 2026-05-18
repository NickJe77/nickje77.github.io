"""
nba_full_rebuild.py
Scrapes full NBA boxscores (player stats) from Basketball Reference.
Saves one JSON file per game under docs/data/basketball/boxscores/
Usage:
    python scripts/nba_full_rebuild.py --start 1976 --end 2025
    python scripts/nba_full_rebuild.py --start 2024 --end 2025 --overwrite
"""

import argparse
import json
import re
import time
import random
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Comment

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "https://www.basketball-reference.com"
OUTPUT_DIR = Path("docs/data/basketball/boxscores")
SCHEDULE_DIR = Path("docs/data/basketball/schedules")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

MIN_DELAY = 3.5
MAX_DELAY = 6.0

STAT_COLUMNS = [
    "mp",
    "fg", "fga", "fg_pct",
    "fg3", "fg3a", "fg3_pct",
    "ft", "fta", "ft_pct",
    "orb", "drb", "trb",
    "ast", "stl", "blk", "tov", "pf", "pts",
    "plus_minus",
]

MONTHS = [
    "october", "november", "december",
    "january", "february", "march",
    "april", "may", "june",
]


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------
def polite_get(url, retries=4):
    for attempt in range(retries):
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 429:
                wait = 60 * (attempt + 1)
                print(f"  Rate limited. Waiting {wait}s ...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            print(f"  Request error ({e}), retrying in 15s ...")
            time.sleep(15)
    raise RuntimeError(f"Failed to fetch {url} after {retries} retries")


# ---------------------------------------------------------------------------
# Schedule scraping
# ---------------------------------------------------------------------------
def get_game_urls_for_season(season):
    cache_path = SCHEDULE_DIR / f"{season}.json"
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    games = []
    for month in MONTHS:
        url = f"{BASE_URL}/leagues/NBA_{season}_games-{month}.html"
        try:
            r = polite_get(url)
        except Exception as e:
            print(f"  Skipping {month} {season}: {e}")
            continue

        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table", {"id": "schedule"})
        if not table:
            continue

        for row in table.find("tbody").find_all("tr"):
            if row.get("class") and "thead" in row.get("class"):
                continue
            box_link = row.find("td", {"data-stat": "box_score_text"})
            if not box_link or not box_link.find("a"):
                continue
            date_th = row.find("th", {"data-stat": "date_game"})
            visitor = row.find("td", {"data-stat": "visitor_team_name"})
            home = row.find("td", {"data-stat": "home_team_name"})
            games.append({
                "date": date_th.get_text(strip=True) if date_th else "",
                "away": visitor.get_text(strip=True) if visitor else "",
                "home": home.get_text(strip=True) if home else "",
                "url": BASE_URL + box_link.find("a")["href"],
            })

    SCHEDULE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(games, f)

    print(f"  Season {season}: {len(games)} games found.")
    return games


# ---------------------------------------------------------------------------
# HTML comment expander  (MUST be defined before parse_player_table)
# ---------------------------------------------------------------------------
def uncomment_html(soup):
    """
    Basketball Reference wraps its stats tables inside HTML comments.
    BeautifulSoup skips comments, so tables appear missing without this step.
    We find every comment containing table markup and splice it back into
    the parse tree as real HTML.
    """
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if "<table" in comment:
            new_soup = BeautifulSoup(comment, "lxml")
            comment.replace_with(new_soup)
    return soup


# ---------------------------------------------------------------------------
# Player table parser  (defined after uncomment_html)
# ---------------------------------------------------------------------------
def parse_player_table(table):
    """Parse one team's basic boxscore table into a list of player stat dicts."""
    players = []
    tbody = table.find("tbody")
    if not tbody:
        return players

    for row in tbody.find_all("tr"):
        if row.get("class") and "thead" in row.get("class"):
            continue

        name_td = row.find("td", {"data-stat": "player"})
        if not name_td:
            continue

        name = name_td.get_text(strip=True)
        if not name:
            continue

        # DNP detection
        reason_td = row.find("td", {"data-stat": "reason"})
        mp_td = row.find("td", {"data-stat": "mp"})
        mp_val = mp_td.get_text(strip=True) if mp_td else ""
        dnp_phrases = ("did not play", "did not dress", "not with team",
                       "player suspended", "dnp")
        if reason_td or mp_val.lower() in dnp_phrases:
            reason = reason_td.get_text(strip=True) if reason_td else (mp_val or "DNP")
            players.append({"player": name, "dnp": reason})
            continue

        player_id = ""
        a_tag = name_td.find("a")
        if a_tag and a_tag.get("href"):
            m = re.search(r"/players/\w/(\w+)\.html", a_tag["href"])
            player_id = m.group(1) if m else ""

        stats = {"player": name, "player_id": player_id}
        for stat in STAT_COLUMNS:
            td = row.find("td", {"data-stat": stat})
            if td is None:
                stats[stat] = None
                continue
            val = td.get_text(strip=True)
            if val in ("", "\u2014", "-"):
                stats[stat] = None
            else:
                try:
                    stats[stat] = float(val) if "." in val else int(val)
                except ValueError:
                    stats[stat] = val

        players.append(stats)

    return players


# ---------------------------------------------------------------------------
# Boxscore scraper
# ---------------------------------------------------------------------------
def scrape_boxscore(game):
    url = game["url"]
    try:
        r = polite_get(url)
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None

    soup = BeautifulSoup(r.text, "lxml")
    soup = uncomment_html(soup)  # expand hidden tables

    game_id_match = re.search(r"/boxscores/([^/]+)\.html", url)
    game_id = game_id_match.group(1) if game_id_match else url.split("/")[-1]

    # Linescore
    final_scores = {}
    linescore = soup.find("table", {"id": "line_score"})
    if linescore:
        thead_rows = linescore.find("thead").find_all("tr")
        quarter_headers = [th.get_text(strip=True) for th in thead_rows[-1].find_all("th")][1:]
        for row in linescore.find("tbody").find_all("tr"):
            cells = row.find_all(["th", "td"])
            team_name = cells[0].get_text(strip=True)
            q_vals = [c.get_text(strip=True) for c in cells[1:]]
            final_scores[team_name] = dict(zip(quarter_headers, q_vals))

    # Player tables
    team_tables = {}
    for table in soup.find_all("table", id=re.compile(r"^box-\w+-game-basic$")):
        m = re.match(r"box-(\w+)-game-basic", table["id"])
        if m:
            team_tables[m.group(1)] = table

    if len(team_tables) < 2:
        print(f"  WARNING: only {len(team_tables)} team table(s) for {game_id}")

    teams_data = {abbr: parse_player_table(tbl) for abbr, tbl in team_tables.items()}

    meta = {
        "game_id": game_id,
        "date": game["date"],
        "away": game["away"],
        "home": game["home"],
        "url": url,
        "linescore": final_scores,
        "teams": teams_data,
    }

    scorebox = soup.find("div", class_="scorebox")
    if scorebox:
        meta_div = scorebox.find("div", class_="scorebox_meta")
        if meta_div:
            for div in meta_div.find_all("div"):
                text = div.get_text(" ", strip=True)
                if "Arena:" in text:
                    meta["arena"] = text.replace("Arena:", "").strip()
                elif "Attendance:" in text:
                    att = text.replace("Attendance:", "").replace(",", "").strip()
                    try:
                        meta["attendance"] = int(att)
                    except ValueError:
                        meta["attendance"] = att

    return meta


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1976)
    parser.add_argument("--end", type=int, default=2025)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCHEDULE_DIR.mkdir(parents=True, exist_ok=True)

    total_scraped = 0
    total_skipped = 0
    total_errors = 0

    for season in range(args.start, args.end + 1):
        print(f"\n=== Season {season} ===")
        games = get_game_urls_for_season(season)

        season_dir = OUTPUT_DIR / str(season)
        season_dir.mkdir(parents=True, exist_ok=True)

        for i, game in enumerate(games, 1):
            game_id = game["url"].split("/")[-1].replace(".html", "")
            out_path = season_dir / f"{game_id}.json"

            if out_path.exists() and not args.overwrite:
                total_skipped += 1
                continue

            print(f"  [{i}/{len(games)}] {game['date']} {game['away']} @ {game['home']} ...", end=" ", flush=True)

            data = scrape_boxscore(game)
            if data is None:
                print("FAILED")
                total_errors += 1
                continue

            with open(out_path, "w") as f:
                json.dump(data, f, indent=2)

            total_scraped += 1
            player_count = sum(len(v) for v in data["teams"].values())
            print(f"OK ({player_count} players)")

    print(f"\nDone. Scraped: {total_scraped} | Skipped: {total_skipped} | Errors: {total_errors}")


if __name__ == "__main__":
    main()
