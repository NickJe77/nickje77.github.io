"""
2026 World Cup Data Fetcher — football-data.org API
=====================================================
Replaces the FBref scraper (which was blocked by Cloudflare).
Uses the free football-data.org REST API — no scraping, no bot detection.

Setup (one time):
  1. Register free at https://www.football-data.org/client/register
  2. Copy your API token
  3. Add it as a GitHub secret named FD_API_TOKEN

Local usage:
  pip install requests
  FD_API_TOKEN=your_token python scripts/scrape_fbref.py

GitHub Actions sets FD_API_TOKEN automatically from your repo secret.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import requests

# ── Config ─────────────────────────────────────────────────────────────────────

API_BASE  = "https://api.football-data.org/v4"
COMP_CODE = "WC"          # football-data.org code for FIFA World Cup
HOST      = "Canada/Mexico/United States"
YEAR      = 2026
DATA_FILE = Path(__file__).parent.parent / "docs" / "data" / "world-cup.json"

TOKEN = os.environ.get("FD_API_TOKEN", "")
if not TOKEN:
    print("ERROR: FD_API_TOKEN environment variable is not set.")
    print("  Register free at https://www.football-data.org/client/register")
    print("  Then: export FD_API_TOKEN=your_token")
    sys.exit(1)

HEADERS = {"X-Auth-Token": TOKEN}

# Rate limit: free tier = 10 req/min  →  wait 7s between calls to be safe
DELAY = 7

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

# ── API helpers ────────────────────────────────────────────────────────────────

def api_get(path: str) -> dict:
    url = f"{API_BASE}{path}"
    print(f"  API {url}")
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 429:
        print("    Rate limited — waiting 60s")
        time.sleep(60)
        r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    time.sleep(DELAY)
    return r.json()


def fed(team: str) -> str:
    return FEDERATIONS.get(team, "")


def cc(team: str) -> str:
    return COUNTRY_CODES.get(team, team[:3].upper())


# ── Match → rows ───────────────────────────────────────────────────────────────

def match_to_rows(match: dict, events: list[dict]) -> list[dict]:
    """
    Convert one football-data.org match + its events into your JSON row format.
    Returns a list of rows (one per goal, header fields on first row only).
    """
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]

    # Score
    ft   = match.get("score", {}).get("fullTime", {})
    hg   = ft.get("home")
    ag   = ft.get("away")

    # Handle AET / penalties
    extra = match.get("score", {}).get("extraTime", {})
    pens  = match.get("score", {}).get("penalties", {})
    duration = match.get("score", {}).get("duration", "REGULAR")

    if hg is None or ag is None:
        score_str = ""
    else:
        score_str = f"{hg}-{ag}"
        if duration == "EXTRA_TIME":
            score_str += " aet"
        if pens.get("home") is not None:
            score_str += f" ({pens['home']}-{pens['away']} pens)"

    # Winner
    winner_code = match.get("score", {}).get("winner")  # HOME_TEAM / AWAY_TEAM / DRAW
    if winner_code == "HOME_TEAM":
        winner = home
    elif winner_code == "AWAY_TEAM":
        winner = away
    else:
        winner = ""

    win_fed = fed(winner) if winner else ""

    # Round label
    stage = match.get("stage", "")
    group = match.get("group", "")
    rnd   = _round_label(stage, group)

    # Separate goal events and card events
    goals: list[dict] = []
    yellow: list[str] = []
    red: list[str]    = []

    for ev in events:
        t    = ev.get("type", "")
        name = ev.get("player", {}).get("name", "") if ev.get("player") else ""
        team = ev.get("team", {}).get("name", "") if ev.get("team") else ""
        minute = ev.get("minute", "")
        extra_min = ev.get("extraMinute")
        if extra_min:
            minute = (minute or 0) + extra_min

        if t == "GOAL":
            detail = ev.get("detail", "")
            og  = " (OG)"   if detail == "Own Goal"     else ""
            pen = " (pen.)" if detail == "Penalty"       else ""
            goals.append({"player": name + og + pen, "team": team, "minute": minute})

        elif t == "CARD":
            detail = ev.get("detail", "")
            label  = f"{name} ({cc(team)})"
            if "YELLOW" in detail.upper():
                yellow.append(label)
            elif "RED" in detail.upper():
                red.append(label)

    # Sort goals by minute
    goals.sort(key=lambda g: g["minute"] if isinstance(g["minute"], int) else 9999)

    # Build rows
    h = a = 0
    rows: list[dict] = []
    first = True

    for g in goals:
        if g["team"] == home:
            h += 1
        else:
            a += 1
        rows.append({
            "Year": YEAR,  "Host": HOST,  "Round": rnd,
            "Team":               home    if first else "",
            "Team__1":            away    if first else "",
            "Final Score":        score_str if first else "",
            "Winnning Team":      winner  if first else "",
            "Winning Federation": win_fed if first else "",
            "Scorers":            f"{g['player']} ({cc(g['team'])})",
            "Time scored":        g["minute"],
            "Progess Score":      f"{h}-{a}",
            "Yellow Cards":       "; ".join(yellow) if first else "",
            "Red Cards":          "; ".join(red)    if first else "",
            "Referee":            "" if first else "",  # not in free tier
        })
        first = False

    # No goals yet (unplayed or 0-0): emit one header row
    if not rows:
        rows = [{
            "Year": YEAR, "Host": HOST, "Round": rnd,
            "Team": home, "Team__1": away,
            "Final Score": score_str, "Winnning Team": winner,
            "Winning Federation": win_fed,
            "Scorers": "", "Time scored": "", "Progess Score": "",
            "Yellow Cards": "; ".join(yellow),
            "Red Cards":    "; ".join(red),
            "Referee": "",
        }]

    return rows


def _round_label(stage: str, group: str) -> str:
    stage_map = {
        "GROUP_STAGE":        f"Group {group.replace('GROUP_', '')}" if group else "Group Stage",
        "LAST_32":            "Round of 32",
        "LAST_16":            "Round of 16",
        "QUARTER_FINALS":     "Quarter-final",
        "SEMI_FINALS":        "Semi-final",
        "THIRD_PLACE":        "Third place",
        "FINAL":              "Final",
    }
    return stage_map.get(stage, stage.replace("_", " ").title())


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
    """Keep all historical rows, replace any existing 2026 rows."""
    historical = [r for r in existing if str(r.get("Year")) != "2026"]
    return historical + new_rows


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("FIFA World Cup 2026 — football-data.org API")
    print("=" * 60)

    # 1. Fetch all matches for the World Cup
    print("\n[1] Fetching all WC matches…")
    data = api_get(f"/competitions/{COMP_CODE}/matches")
    matches = data.get("matches", [])
    print(f"    Got {len(matches)} matches")

    if not matches:
        print("No matches returned — check your token or competition code.")
        sys.exit(1)

    # 2. For each FINISHED match, fetch its events
    print("\n[2] Fetching events for completed matches…")
    all_new_rows: list[dict] = []
    finished = [m for m in matches if m.get("status") == "FINISHED"]
    print(f"    {len(finished)} completed matches to process")

    for i, match in enumerate(finished, 1):
        home  = match["homeTeam"]["name"]
        away  = match["awayTeam"]["name"]
        mid   = match["id"]
        stage = match.get("stage", "")
        group = match.get("group", "")
        print(f"\n  [{i}/{len(finished)}] {home} vs {away}  ({_round_label(stage, group)})")

        try:
            ev_data = api_get(f"/matches/{mid}")
            events  = ev_data.get("match", {}).get("goals", [])
            # football-data.org v4: goals are a top-level key in the match detail
            if not events:
                events = ev_data.get("goals", [])
            # Also grab bookings for cards
            bookings = ev_data.get("match", {}).get("bookings", []) or ev_data.get("bookings", [])
            # Merge goals + bookings into one events list with a "type" field
            all_events = []
            for g in events:
                all_events.append({**g, "type": "GOAL"})
            for b in bookings:
                all_events.append({**b, "type": "CARD"})
        except Exception as e:
            print(f"    ✗ Events fetch failed: {e} — using match summary only")
            all_events = []

        rows = match_to_rows(match, all_events)
        all_new_rows.extend(rows)
        goals = sum(1 for r in rows if r["Scorers"])
        print(f"    → {goals} goal(s), {len(rows)} row(s)")

    # 3. Merge & save
    print(f"\n[3] Merging with existing data…")
    existing = load_existing()
    merged   = merge(existing, all_new_rows)
    save(merged)

    total_goals = sum(1 for r in all_new_rows if r["Scorers"])
    print(f"    2026 matches: {len(finished)}  |  goal events: {total_goals}")


if __name__ == "__main__":
    main()
