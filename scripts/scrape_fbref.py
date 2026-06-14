"""
FBref 2026 World Cup Scraper
=============================
Scrapes https://fbref.com for every 2026 World Cup match and merges the
results into data/world-cup.json in the exact same row-per-event format
as the existing historical data.

Field mapping:
  Year              → 2026
  Host              → "Canada/Mexico/United States"
  Round             → e.g. "Group A", "Final"
  Team              → home team  (only on 1st row of each match)
  Team__1           → away team  (only on 1st row)
  Final Score       → e.g. "2-0", "3-3 aet"  (only on 1st row)
  Winnning Team     → winner or "" for draw    (only on 1st row)
  Winning Federation→ confederation of winner  (only on 1st row)
  Scorers           → "Player Name (XXX)"  — one scorer per row
  Time scored       → integer minute
  Progess Score     → "1-0", "2-1" etc.
  Yellow Cards      → "Player (XXX); Player (XXX)"  (only on 1st row)
  Red Cards         → same format               (only on 1st row)
  Referee           → "Name (NAT)"              (only on 1st row)

Usage:
  pip install requests beautifulsoup4
  python scripts/scrape_fbref.py
"""

import json
import re
import time
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────

BASE        = "https://fbref.com"
FIXTURES_URL = f"{BASE}/en/comps/1/schedule/World-Cup-Scores-and-Fixtures"
HOST        = "Canada/Mexico/United States"
YEAR        = 2026
DATA_FILE   = Path(__file__).parent.parent / "docs" / "data" / "world-cup.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Seconds between requests — FBref rate-limits aggressively; keep this >= 4
DELAY = 5

# ── Federation lookup ─────────────────────────────────────────────────────────

FEDERATIONS: dict[str, str] = {
    # CONMEBOL
    "Argentina":"CONMEBOL","Brazil":"CONMEBOL","Uruguay":"CONMEBOL",
    "Colombia":"CONMEBOL","Ecuador":"CONMEBOL","Chile":"CONMEBOL",
    "Paraguay":"CONMEBOL","Peru":"CONMEBOL","Venezuela":"CONMEBOL","Bolivia":"CONMEBOL",
    # CONCACAF
    "United States":"CONCACAF","Mexico":"CONCACAF","Canada":"CONCACAF",
    "Costa Rica":"CONCACAF","Honduras":"CONCACAF","Panama":"CONCACAF",
    "Jamaica":"CONCACAF","Trinidad and Tobago":"CONCACAF","Haiti":"CONCACAF",
    "El Salvador":"CONCACAF","Curaçao":"CONCACAF",
    # UEFA
    "France":"UEFA","Germany":"UEFA","Spain":"UEFA","Italy":"UEFA","England":"UEFA",
    "Netherlands":"UEFA","Portugal":"UEFA","Belgium":"UEFA","Croatia":"UEFA",
    "Switzerland":"UEFA","Denmark":"UEFA","Sweden":"UEFA","Norway":"UEFA",
    "Poland":"UEFA","Czech Republic":"UEFA","Czechia":"UEFA","Austria":"UEFA",
    "Scotland":"UEFA","Wales":"UEFA","Serbia":"UEFA","Hungary":"UEFA",
    "Ukraine":"UEFA","Turkey":"UEFA","Greece":"UEFA","Romania":"UEFA",
    "Slovakia":"UEFA","Slovenia":"UEFA","Albania":"UEFA","Iceland":"UEFA",
    "Finland":"UEFA","Bosnia and Herzegovina":"UEFA","Georgia":"UEFA",
    "North Macedonia":"UEFA",
    # CAF
    "Morocco":"CAF","Senegal":"CAF","Nigeria":"CAF","Ghana":"CAF","Cameroon":"CAF",
    "Tunisia":"CAF","Algeria":"CAF","South Africa":"CAF","Egypt":"CAF","Mali":"CAF",
    "DR Congo":"CAF","Ivory Coast":"CAF","Côte d'Ivoire":"CAF","Cape Verde":"CAF",
    # AFC
    "Japan":"AFC","South Korea":"AFC","Korea Republic":"AFC","Iran":"AFC",
    "Saudi Arabia":"AFC","Australia":"AFC","Qatar":"AFC","Iraq":"AFC",
    "China":"AFC","Uzbekistan":"AFC","Jordan":"AFC","Bahrain":"AFC",
    # OFC
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

# ── Helpers ───────────────────────────────────────────────────────────────────

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get(url: str) -> BeautifulSoup:
    print(f"  GET {url}")
    r = SESSION.get(url, timeout=20)
    r.raise_for_status()
    time.sleep(DELAY)
    return BeautifulSoup(r.text, "html.parser")


def code(team: str) -> str:
    return COUNTRY_CODES.get(team, team[:3].upper())


def federation(team: str) -> str:
    return FEDERATIONS.get(team, "")


def parse_minute(raw: str) -> int | str:
    """'45+2' → 47, '8' → 8, '' → ''"""
    raw = raw.strip().rstrip("'′")
    if not raw:
        return ""
    m = re.match(r"^(\d+)(?:\+(\d+))?", raw)
    if not m:
        return raw
    base = int(m.group(1))
    extra = int(m.group(2)) if m.group(2) else 0
    return base + extra


def parse_score(score: str) -> tuple[int, int]:
    """'2–1' or '2-1' → (2, 1). Returns (-1,-1) on failure."""
    m = re.match(r"(\d+)\s*[–\-]\s*(\d+)", score or "")
    return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)


def winner_from_score(team1: str, team2: str, score: str) -> str:
    """Return winning team name, or '' for draws (before penalties)."""
    # Strip AET / pen notation
    clean = re.sub(r"\s*\(.*?\)", "", score or "")
    clean = re.sub(r"\s*(a\.?e\.?t\.?|aet|pens?\.?)", "", clean, flags=re.I).strip()
    g1, g2 = parse_score(clean)
    if g1 == -1:
        return ""
    if g1 > g2:
        return team1
    if g2 > g1:
        return team2
    # If pens in original: look for bracketed pen score
    pen = re.search(r"\((\d+)[–\-](\d+)\)", score or "")
    if pen:
        p1, p2 = int(pen.group(1)), int(pen.group(2))
        return team1 if p1 > p2 else team2
    return ""


# ── FBref schedule page → match links ────────────────────────────────────────

def get_match_links() -> list[dict]:
    """
    Scrape the main schedule page.
    Returns list of {round, team1, team2, score, match_url}
    """
    soup = get(FIXTURES_URL)

    # FBref wraps the table in a div whose id starts with "div_sched"
    table = soup.find("table", id=re.compile(r"sched"))
    if not table:
        # Sometimes it's inside a comment — FBref hides some tables in HTML comments
        import html
        full = str(soup)
        # Extract commented tables
        comments = re.findall(r"<!--(.*?)-->", full, re.DOTALL)
        for c in comments:
            inner = BeautifulSoup(c, "html.parser")
            table = inner.find("table", id=re.compile(r"sched"))
            if table:
                break

    if not table:
        print("  ⚠ Could not find schedule table on fixtures page")
        return []

    matches = []
    for row in table.find_all("tr"):
        cells = {td.get("data-stat"): td for td in row.find_all(["td", "th"])}
        if not cells:
            continue

        # Round / stage
        rnd_cell  = cells.get("round") or cells.get("comp_round")
        home_cell = cells.get("home_team") or cells.get("squad_a")
        away_cell = cells.get("away_team") or cells.get("squad_b")
        score_cell = cells.get("score")
        link_cell  = score_cell  # score cell usually holds the match-report link

        if not (home_cell and away_cell):
            continue

        team1 = home_cell.get_text(strip=True)
        team2 = away_cell.get_text(strip=True)
        score = score_cell.get_text(strip=True) if score_cell else ""
        rnd   = rnd_cell.get_text(strip=True) if rnd_cell else "Unknown"

        # Match report URL
        match_url = ""
        if link_cell:
            a = link_cell.find("a", href=re.compile(r"/en/matches/"))
            if a:
                match_url = BASE + a["href"]

        if team1 and team2:
            matches.append({
                "round": rnd,
                "team1": team1,
                "team2": team2,
                "score": score,
                "match_url": match_url,
            })

    print(f"  Found {len(matches)} match rows on schedule page")
    return matches


# ── Individual match report page ──────────────────────────────────────────────

def scrape_match_report(match: dict) -> list[dict]:
    """
    Scrape one FBref match report page.
    Returns list of JSON rows in your data format.
    """
    if not match["match_url"]:
        return _no_goals_row(match)

    try:
        soup = get(match["match_url"])
    except Exception as e:
        print(f"    ✗ {e}")
        return _no_goals_row(match)

    team1  = match["team1"]
    team2  = match["team2"]
    score  = match["score"]
    rnd    = match["round"]

    # ── Scorers / events ─────────────────────────────────────────────────────
    # FBref match pages have a "div_events_wrap" or similar section listing
    # each goal with player name, team, and minute.

    events: list[dict] = []

    events_div = soup.find("div", id=re.compile(r"event"))
    if events_div:
        # Each event block: look for elements that contain goal/card info
        for ev in events_div.find_all("div", class_=re.compile(r"event")):
            text = ev.get_text(" ", strip=True)

            # Determine which side
            side_class = ev.get("class", [])
            is_home = any("home" in c or "a_" in c for c in side_class)
            team = team1 if is_home else team2

            # Minute
            min_match = re.search(r"(\d{1,3}(?:\+\d+)?)'", text)
            minute = parse_minute(min_match.group(1)) if min_match else ""

            # Skip non-goal events (substitutions, cards only)
            if not re.search(r"goal|⚽|gol", text, re.I):
                continue

            # Player name — strip minute and symbols
            player = re.sub(r"\d{1,3}(?:\+\d+)?'", "", text)
            player = re.sub(r"[⚽🟨🟥]", "", player).strip(" ,–")
            # Own goal
            og = ""
            if re.search(r"\(o\.?g\.?\)|own goal", player, re.I):
                og = " (OG)"
                player = re.sub(r"\(o\.?g\.?\)|own goal", "", player, flags=re.I).strip()
            pen = ""
            if re.search(r"\(pen\.?\)|penalty", player, re.I):
                pen = " (pen.)"
                player = re.sub(r"\(pen\.?\)|penalty", "", player, flags=re.I).strip()

            if player:
                events.append({"player": player + og + pen, "team": team, "minute": minute})

    # ── Fallback: parse "div_scores" shot tables for goals ───────────────────
    # If event div wasn't found or returned nothing, try the shot/goal tables
    if not events:
        for tbl in soup.find_all("table", id=re.compile(r"shot")):
            for row in tbl.find_all("tr"):
                cells = {td.get("data-stat"): td for td in row.find_all("td")}
                if cells.get("outcome") and cells["outcome"].get_text(strip=True) == "Goal":
                    player_td = cells.get("player")
                    min_td    = cells.get("minute")
                    team_td   = cells.get("squad")
                    player = player_td.get_text(strip=True) if player_td else ""
                    minute = parse_minute(min_td.get_text(strip=True) if min_td else "")
                    team   = team_td.get_text(strip=True) if team_td else ""
                    if player:
                        events.append({"player": player, "team": team, "minute": minute})

    # ── Cards ─────────────────────────────────────────────────────────────────
    yellow_cards: list[str] = []
    red_cards: list[str]    = []

    for tbl in soup.find_all("table", id=re.compile(r"misc")):
        for row in tbl.find_all("tr"):
            cells = {td.get("data-stat"): td for td in row.find_all("td")}
            player_td  = cells.get("player")
            yellow_td  = cells.get("cards_yellow")
            red_td     = cells.get("cards_red")
            squad_td   = cells.get("squad")
            if not player_td:
                continue
            pname = player_td.get_text(strip=True)
            nation = squad_td.get_text(strip=True) if squad_td else ""
            if yellow_td and yellow_td.get_text(strip=True) not in ("", "0"):
                yellow_cards.append(f"{pname} ({code(nation)})")
            if red_td and red_td.get_text(strip=True) not in ("", "0"):
                red_cards.append(f"{pname} ({code(nation)})")

    # ── Referee ───────────────────────────────────────────────────────────────
    referee = ""
    for strong in soup.find_all("strong"):
        if "Referee" in strong.get_text():
            sibling = strong.next_sibling
            if sibling:
                referee = str(sibling).strip().lstrip(":").strip()
            break
    # Also try the scorebox meta section
    if not referee:
        for div in soup.find_all("div", id=re.compile(r"content|scorebox")):
            m = re.search(r"Referee[:\s]+([^\n<]+)", div.get_text())
            if m:
                referee = m.group(1).strip()
                break

    return _build_rows(team1, team2, score, rnd, events, yellow_cards, red_cards, referee)


# ── Row builder ───────────────────────────────────────────────────────────────

def _build_rows(
    team1: str, team2: str, score: str, rnd: str,
    events: list[dict],
    yellow_cards: list[str], red_cards: list[str],
    referee: str
) -> list[dict]:

    winner  = winner_from_score(team1, team2, score)
    win_fed = federation(winner) if winner else ""

    # Sort events by minute
    def sort_key(e):
        m = e["minute"]
        return m if isinstance(m, int) else 9999

    events.sort(key=sort_key)

    # Build running score
    h, a = 0, 0
    rows = []
    first = True

    for ev in events:
        if ev["team"] == team1:
            h += 1
        else:
            a += 1

        row = {
            "Year": YEAR,
            "Host": HOST,
            "Round": rnd,
            "Team":            team1  if first else "",
            "Team__1":         team2  if first else "",
            "Final Score":     score  if first else "",
            "Winnning Team":   winner if first else "",
            "Winning Federation": win_fed if first else "",
            "Scorers":         f"{ev['player']} ({code(ev['team'])})",
            "Time scored":     ev["minute"],
            "Progess Score":   f"{h}-{a}",
            "Yellow Cards":    "; ".join(yellow_cards) if first else "",
            "Red Cards":       "; ".join(red_cards)    if first else "",
            "Referee":         referee if first else "",
        }
        rows.append(row)
        first = False

    # No goals parsed — emit a single header row so the match is still recorded
    if not rows:
        rows = [_no_goals_row_raw(team1, team2, score, rnd, winner, win_fed,
                                  yellow_cards, red_cards, referee)]

    return rows


def _no_goals_row(match: dict) -> list[dict]:
    team1, team2, score, rnd = match["team1"], match["team2"], match["score"], match["round"]
    winner  = winner_from_score(team1, team2, score)
    win_fed = federation(winner) if winner else ""
    return [_no_goals_row_raw(team1, team2, score, rnd, winner, win_fed, [], [], "")]


def _no_goals_row_raw(team1, team2, score, rnd, winner, win_fed, yc, rc, ref) -> dict:
    return {
        "Year": YEAR, "Host": HOST, "Round": rnd,
        "Team": team1, "Team__1": team2,
        "Final Score": score, "Winnning Team": winner,
        "Winning Federation": win_fed,
        "Scorers": "", "Time scored": "", "Progess Score": "",
        "Yellow Cards": "; ".join(yc), "Red Cards": "; ".join(rc),
        "Referee": ref,
    }


# ── Merge into existing world-cup.json ───────────────────────────────────────

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
    """
    Replace any existing 2026 rows with freshly scraped ones,
    then append the new rows after all historical data.
    """
    historical = [r for r in existing if str(r.get("Year")) != "2026"]
    return historical + new_rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("FIFA World Cup 2026 — FBref Scraper")
    print("=" * 60)

    print("\n[1] Fetching match schedule from FBref…")
    matches = get_match_links()

    if not matches:
        print("No matches found — aborting.")
        sys.exit(1)

    print(f"\n[2] Scraping {len(matches)} match report pages…")
    all_new_rows: list[dict] = []

    for i, match in enumerate(matches, 1):
        label = f"{match['team1']} vs {match['team2']} ({match['round']})"
        print(f"\n  [{i}/{len(matches)}] {label}")

        # Skip future matches (no score yet)
        if not match["score"] or match["score"] in ("-", ""):
            print("    → No score yet, skipping detail scrape")
            continue

        rows = scrape_match_report(match)
        all_new_rows.extend(rows)
        print(f"    → {len(rows)} row(s)")

    print(f"\n[3] Merging with existing data in {DATA_FILE}…")
    existing = load_existing()
    print(f"    Existing rows: {len(existing)}  |  New 2026 rows: {len(all_new_rows)}")
    merged = merge(existing, all_new_rows)
    save(merged)

    goals  = sum(1 for r in all_new_rows if r["Scorers"])
    matches_with_score = sum(1 for r in all_new_rows if r["Team"])
    print(f"\n    2026 matches recorded: {matches_with_score}")
    print(f"    2026 goal events:      {goals}")


if __name__ == "__main__":
    main()
