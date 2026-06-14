"""
FBref 2026 World Cup Scraper
=============================
Uses Playwright (headless Chromium) to bypass FBref's bot detection.
Scrapes every 2026 World Cup match and merges results into
docs/data/world-cup.json in the exact same row-per-event format
as the existing historical data.

Usage:
  pip install playwright beautifulsoup4
  playwright install chromium
  python scripts/scrape_fbref.py
"""

import json
import re
import time
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ── Config ─────────────────────────────────────────────────────────────────────

BASE         = "https://fbref.com"
FIXTURES_URL = f"{BASE}/en/comps/1/schedule/World-Cup-Scores-and-Fixtures"
HOST         = "Canada/Mexico/United States"
YEAR         = 2026
DATA_FILE    = Path(__file__).parent.parent / "docs" / "data" / "world-cup.json"

# Seconds between page loads — be polite, avoid bans
DELAY = 6

# ── Lookups ────────────────────────────────────────────────────────────────────

FEDERATIONS: dict[str, str] = {
    "Argentina":"CONMEBOL","Brazil":"CONMEBOL","Uruguay":"CONMEBOL",
    "Colombia":"CONMEBOL","Ecuador":"CONMEBOL","Chile":"CONMEBOL",
    "Paraguay":"CONMEBOL","Peru":"CONMEBOL","Venezuela":"CONMEBOL","Bolivia":"CONMEBOL",
    "United States":"CONCACAF","Mexico":"CONCACAF","Canada":"CONCACAF",
    "Costa Rica":"CONCACAF","Honduras":"CONCACAF","Panama":"CONCACAF",
    "Jamaica":"CONCACAF","Trinidad and Tobago":"CONCACAF","Haiti":"CONCACAF",
    "El Salvador":"CONCACAF","Curaçao":"CONCACAF",
    "France":"UEFA","Germany":"UEFA","Spain":"UEFA","Italy":"UEFA","England":"UEFA",
    "Netherlands":"UEFA","Portugal":"UEFA","Belgium":"UEFA","Croatia":"UEFA",
    "Switzerland":"UEFA","Denmark":"UEFA","Sweden":"UEFA","Norway":"UEFA",
    "Poland":"UEFA","Czech Republic":"UEFA","Czechia":"UEFA","Austria":"UEFA",
    "Scotland":"UEFA","Wales":"UEFA","Serbia":"UEFA","Hungary":"UEFA",
    "Ukraine":"UEFA","Turkey":"UEFA","Greece":"UEFA","Romania":"UEFA",
    "Slovakia":"UEFA","Slovenia":"UEFA","Albania":"UEFA","Iceland":"UEFA",
    "Finland":"UEFA","Bosnia and Herzegovina":"UEFA","Georgia":"UEFA",
    "North Macedonia":"UEFA",
    "Morocco":"CAF","Senegal":"CAF","Nigeria":"CAF","Ghana":"CAF","Cameroon":"CAF",
    "Tunisia":"CAF","Algeria":"CAF","South Africa":"CAF","Egypt":"CAF","Mali":"CAF",
    "DR Congo":"CAF","Ivory Coast":"CAF","Côte d'Ivoire":"CAF","Cape Verde":"CAF",
    "Japan":"AFC","South Korea":"AFC","Korea Republic":"AFC","Iran":"AFC",
    "Saudi Arabia":"AFC","Australia":"AFC","Qatar":"AFC","Iraq":"AFC",
    "China":"AFC","Uzbekistan":"AFC","Jordan":"AFC","Bahrain":"AFC",
    "New Zealand":"OFC",
}

COUNTRY_CODES: dict[str, str] = {
    "Argentina":"ARG","Brazil":"BRA","France":"FRA","Germany":"GER","Spain":"ESP",
    "Italy":"ITA","England":"ENG","Netherlands":"NED","Portugal":"POR",
    "Croatia":"CRO","Morocco":"MAR","Senegal":"SEN","Japan":"JPN",
    "South Korea":"KOR","Korea Republic":"KOR","Australia":"AUS","Mexico":"MEX",
    "United States":"USA","Canada":"CAN","Uruguay":"URU","Colombia":"COL",
    "Ecuador":"ECU","Belgium":"BEL","Switzerland":"SUI","Denmark":"DEN",
    "Sweden":"SWE","Poland":"POL","Czech Republic":"CZE","Czechia":"CZE",
    "Serbia":"SRB","Ukraine":"UKR","Turkey":"TUR","Iran":"IRN","Saudi Arabia":"KSA",
    "Qatar":"QAT","Nigeria":"NGA","Ghana":"GHA","Cameroon":"CMR",
    "South Africa":"RSA","Tunisia":"TUN","Algeria":"DZA","Egypt":"EGY",
    "Paraguay":"PAR","Chile":"CHI","Peru":"PER","Bolivia":"BOL","Venezuela":"VEN",
    "Costa Rica":"CRC","Honduras":"HON","Panama":"PAN","Jamaica":"JAM",
    "Haiti":"HAI","Curaçao":"CUW","Uzbekistan":"UZB","Jordan":"JOR",
    "Cape Verde":"CPV","DR Congo":"COD","Iraq":"IRQ","New Zealand":"NZL",
    "Bosnia and Herzegovina":"BIH","Georgia":"GEO","Albania":"ALB",
}

# ── Playwright browser wrapper ─────────────────────────────────────────────────

_browser = None
_page    = None

def init_browser(pw):
    global _browser, _page
    _browser = pw.chromium.launch(headless=True)
    context  = _browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 900},
        locale="en-US",
    )
    # Block images/fonts/media to speed things up
    context.route(
        "**/*",
        lambda route: route.abort()
        if route.request.resource_type in ("image", "media", "font", "stylesheet")
        else route.continue_(),
    )
    _page = context.new_page()


def fetch_html(url: str) -> BeautifulSoup:
    """Load a page with Playwright and return parsed HTML."""
    global _page
    print(f"  FETCH {url}")
    try:
        _page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        # Wait for the main content table to appear
        try:
            _page.wait_for_selector("table", timeout=10_000)
        except PWTimeout:
            pass
    except PWTimeout:
        print("    ⚠ Page load timeout — using whatever loaded")

    html = _page.content()
    time.sleep(DELAY)
    return BeautifulSoup(html, "html.parser")


# ── Pure helpers ───────────────────────────────────────────────────────────────

def code(team: str) -> str:
    return COUNTRY_CODES.get(team, team[:3].upper())


def federation(team: str) -> str:
    return FEDERATIONS.get(team, "")


def parse_minute(raw: str) -> int | str:
    raw = str(raw).strip().rstrip("'′")
    if not raw:
        return ""
    m = re.match(r"^(\d+)(?:\+(\d+))?", raw)
    if not m:
        return raw
    return int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)


def parse_score(score: str) -> tuple[int, int]:
    m = re.match(r"(\d+)\s*[–\-]\s*(\d+)", score or "")
    return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)


def winner_from_score(team1: str, team2: str, score: str) -> str:
    clean = re.sub(r"\s*\(.*?\)", "", score or "")
    clean = re.sub(r"\s*(a\.?e\.?t\.?|aet|pens?\.?)", "", clean, flags=re.I).strip()
    g1, g2 = parse_score(clean)
    if g1 == -1:
        return ""
    if g1 > g2:
        return team1
    if g2 > g1:
        return team2
    pen = re.search(r"\((\d+)[–\-](\d+)\)", score or "")
    if pen:
        p1, p2 = int(pen.group(1)), int(pen.group(2))
        return team1 if p1 > p2 else team2
    return ""


# ── Schedule page ──────────────────────────────────────────────────────────────

def get_match_links(soup: BeautifulSoup) -> list[dict]:
    """Parse the fixtures page and return match metadata + report URLs."""
    # FBref sometimes hides the table inside an HTML comment
    table = soup.find("table", id=re.compile(r"sched"))
    if not table:
        for comment in soup.find_all(string=re.compile(r"<table")):
            inner = BeautifulSoup(str(comment), "html.parser")
            table = inner.find("table", id=re.compile(r"sched"))
            if table:
                break

    if not table:
        print("  ⚠ Schedule table not found — dumping page snippet for debug:")
        print(soup.get_text()[:500])
        return []

    matches = []
    for row in table.find_all("tr"):
        cells = {td.get("data-stat"): td for td in row.find_all(["td", "th"])}
        if not cells:
            continue

        home_cell  = cells.get("home_team") or cells.get("squad_a")
        away_cell  = cells.get("away_team") or cells.get("squad_b")
        score_cell = cells.get("score")
        rnd_cell   = cells.get("round") or cells.get("comp_round")

        if not (home_cell and away_cell):
            continue

        team1 = home_cell.get_text(strip=True)
        team2 = away_cell.get_text(strip=True)
        if not team1 or not team2:
            continue

        score = score_cell.get_text(strip=True) if score_cell else ""
        rnd   = rnd_cell.get_text(strip=True)   if rnd_cell   else "Unknown"

        match_url = ""
        if score_cell:
            a = score_cell.find("a", href=re.compile(r"/en/matches/"))
            if a:
                match_url = BASE + a["href"]

        matches.append({
            "round": rnd, "team1": team1, "team2": team2,
            "score": score, "match_url": match_url,
        })

    return matches


# ── Match report page ──────────────────────────────────────────────────────────

def scrape_match_report(match: dict, soup: BeautifulSoup) -> list[dict]:
    team1, team2 = match["team1"], match["team2"]
    score, rnd   = match["score"], match["round"]

    # ── Goal events ───────────────────────────────────────────────────────────
    events: list[dict] = []

    # Method 1: div#events_wrap or similar event timeline
    events_div = soup.find("div", id=re.compile(r"events?_wrap|event"))
    if events_div:
        for ev in events_div.find_all("div", class_=re.compile(r"event")):
            text = ev.get_text(" ", strip=True)
            if not re.search(r"goal|⚽", text, re.I):
                continue
            classes = " ".join(ev.get("class", []))
            is_home = bool(re.search(r"home|team_a|a_", classes))
            team = team1 if is_home else team2
            min_m = re.search(r"(\d{1,3}(?:\+\d+)?)'?", text)
            minute = parse_minute(min_m.group(1)) if min_m else ""
            player = re.sub(r"\d{1,3}(?:\+\d+)?'?|[⚽🟨🟥]", "", text).strip(" ,–")
            og  = " (OG)"  if re.search(r"own.goal|o\.g\.", player, re.I) else ""
            pen = " (pen.)" if re.search(r"pen\.|penalty",  player, re.I) else ""
            player = re.sub(r"own.goal|o\.g\.|pen\.|penalty", "", player, flags=re.I).strip()
            if player:
                events.append({"player": player + og + pen, "team": team, "minute": minute})

    # Method 2: shots table (data-stat="outcome" == "Goal")
    if not events:
        for tbl in soup.find_all("table", id=re.compile(r"shot")):
            for row in tbl.find_all("tr"):
                cells = {td.get("data-stat"): td for td in row.find_all("td")}
                if not cells.get("outcome"):
                    continue
                if cells["outcome"].get_text(strip=True) != "Goal":
                    continue
                player = cells["player"].get_text(strip=True) if cells.get("player") else ""
                minute = parse_minute(cells["minute"].get_text(strip=True) if cells.get("minute") else "")
                squad  = cells["squad"].get_text(strip=True)  if cells.get("squad")  else ""
                if player:
                    events.append({"player": player, "team": squad, "minute": minute})

    # ── Cards ─────────────────────────────────────────────────────────────────
    yellow_cards: list[str] = []
    red_cards: list[str]    = []

    for tbl in soup.find_all("table", id=re.compile(r"misc")):
        for row in tbl.find_all("tr"):
            cells = {td.get("data-stat"): td for td in row.find_all("td")}
            if not cells.get("player"):
                continue
            pname  = cells["player"].get_text(strip=True)
            nation = cells["squad"].get_text(strip=True) if cells.get("squad") else ""
            yel    = cells["cards_yellow"].get_text(strip=True) if cells.get("cards_yellow") else "0"
            red    = cells["cards_red"].get_text(strip=True)    if cells.get("cards_red")    else "0"
            if yel not in ("", "0"):
                yellow_cards.append(f"{pname} ({code(nation)})")
            if red not in ("", "0"):
                red_cards.append(f"{pname} ({code(nation)})")

    # ── Referee ───────────────────────────────────────────────────────────────
    referee = ""
    text = soup.get_text(" ")
    m = re.search(r"Referee[:\s]+([A-ZÀ-Ž][^\n,<]{3,40})", text)
    if m:
        referee = m.group(1).strip()

    return _build_rows(team1, team2, score, rnd, events, yellow_cards, red_cards, referee)


# ── Row builder ────────────────────────────────────────────────────────────────

def _build_rows(team1, team2, score, rnd, events, yellow_cards, red_cards, referee) -> list[dict]:
    winner  = winner_from_score(team1, team2, score)
    win_fed = federation(winner) if winner else ""

    events.sort(key=lambda e: e["minute"] if isinstance(e["minute"], int) else 9999)

    h = a = 0
    rows: list[dict] = []
    first = True

    for ev in events:
        if ev["team"] == team1:
            h += 1
        else:
            a += 1
        rows.append({
            "Year": YEAR,  "Host": HOST,  "Round": rnd,
            "Team":             team1  if first else "",
            "Team__1":          team2  if first else "",
            "Final Score":      score  if first else "",
            "Winnning Team":    winner if first else "",
            "Winning Federation": win_fed if first else "",
            "Scorers":          f"{ev['player']} ({code(ev['team'])})",
            "Time scored":      ev["minute"],
            "Progess Score":    f"{h}-{a}",
            "Yellow Cards":     "; ".join(yellow_cards) if first else "",
            "Red Cards":        "; ".join(red_cards)    if first else "",
            "Referee":          referee if first else "",
        })
        first = False

    if not rows:
        rows = [{
            "Year": YEAR, "Host": HOST, "Round": rnd,
            "Team": team1, "Team__1": team2,
            "Final Score": score, "Winnning Team": winner,
            "Winning Federation": win_fed,
            "Scorers": "", "Time scored": "", "Progess Score": "",
            "Yellow Cards": "; ".join(yellow_cards),
            "Red Cards":    "; ".join(red_cards),
            "Referee": referee,
        }]
    return rows


# ── JSON merge ─────────────────────────────────────────────────────────────────

def load_existing() -> list[dict]:
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save(data: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Saved {len(data)} total rows → {DATA_FILE}")


def merge(existing: list[dict], new_rows: list[dict]) -> list[dict]:
    historical = [r for r in existing if str(r.get("Year")) != "2026"]
    return historical + new_rows


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("FIFA World Cup 2026 — FBref Scraper (Playwright)")
    print("=" * 60)

    with sync_playwright() as pw:
        init_browser(pw)

        print("\n[1] Fetching match schedule…")
        soup = fetch_html(FIXTURES_URL)
        matches = get_match_links(soup)

        if not matches:
            print("No matches found — aborting.")
            sys.exit(1)

        print(f"    Found {len(matches)} matches on schedule page")

        print(f"\n[2] Scraping match reports…")
        all_new_rows: list[dict] = []

        for i, match in enumerate(matches, 1):
            label = f"{match['team1']} vs {match['team2']} ({match['round']})"
            print(f"\n  [{i}/{len(matches)}] {label}")

            # Skip unplayed matches
            if not match["score"] or match["score"].strip() in ("", "-"):
                print("    → No score yet, skipping")
                continue

            if not match["match_url"]:
                print("    → No report URL, recording header only")
                all_new_rows.extend(_build_rows(
                    match["team1"], match["team2"], match["score"],
                    match["round"], [], [], [], ""
                ))
                continue

            try:
                report_soup = fetch_html(match["match_url"])
                rows = scrape_match_report(match, report_soup)
                all_new_rows.extend(rows)
                goals = sum(1 for r in rows if r["Scorers"])
                print(f"    → {goals} goal(s), {len(rows)} row(s)")
            except Exception as e:
                print(f"    ✗ Error: {e} — recording header only")
                all_new_rows.extend(_build_rows(
                    match["team1"], match["team2"], match["score"],
                    match["round"], [], [], [], ""
                ))

        _browser.close()

    print(f"\n[3] Merging with existing data…")
    existing = load_existing()
    merged   = merge(existing, all_new_rows)
    save(merged)

    goals   = sum(1 for r in all_new_rows if r["Scorers"])
    headers = sum(1 for r in all_new_rows if r["Team"])
    print(f"    2026 matches: {headers}  |  goal events: {goals}")


if __name__ == "__main__":
    main()
