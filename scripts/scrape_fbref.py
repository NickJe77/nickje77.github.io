"""
2026 World Cup Data Fetcher — openfootball/worldcup.json
=========================================================
Source: https://github.com/openfootball/worldcup.json
  → raw file: https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json

No API key. No signup. No scraping. No bot detection.
Just a plain GET to a public GitHub raw file updated daily by the maintainer.

Source JSON shape (one match):
{
  "round": "Matchday 1",
  "date": "2026-06-11",
  "team1": "Mexico",
  "team2": "South Africa",
  "score": {"ft": [2, 0], "ht": [1, 0]},
  "goals1": [{"name": "Julián Quiñones", "minute": "9"},
              {"name": "Raúl Jiménez",   "minute": "67"}],
  "goals2": [],
  "group": "Group A"
}

Usage:
  pip install requests
  python scripts/scrape_fbref.py
"""

import json
import re
import sys
import time
from pathlib import Path

import requests

# ── Config ─────────────────────────────────────────────────────────────────────

SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "openfootball/worldcup.json/master/2026/worldcup.json"
)
HOST      = "Canada/Mexico/United States"
YEAR      = 2026
DATA_FILE = Path(__file__).parent.parent / "docs" / "data" / "world-cup.json"

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
    "Poland":"UEFA","Czech Republic":"UEFA","Czechia":"UEFA","Czech Republic":"UEFA",
    "Austria":"UEFA","Scotland":"UEFA","Wales":"UEFA","Serbia":"UEFA",
    "Hungary":"UEFA","Ukraine":"UEFA","Turkey":"UEFA","Greece":"UEFA",
    "Romania":"UEFA","Slovakia":"UEFA","Slovenia":"UEFA","Albania":"UEFA",
    "Iceland":"UEFA","Finland":"UEFA","Bosnia and Herzegovina":"UEFA",
    "Bosnia & Herzegovina":"UEFA","Georgia":"UEFA","North Macedonia":"UEFA",
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
    "South Korea":"KOR","Australia":"AUS","Mexico":"MEX","United States":"USA",
    "Canada":"CAN","Uruguay":"URU","Colombia":"COL","Ecuador":"ECU",
    "Belgium":"BEL","Switzerland":"SUI","Denmark":"DEN","Sweden":"SWE",
    "Poland":"POL","Czech Republic":"CZE","Czechia":"CZE","Serbia":"SRB",
    "Ukraine":"UKR","Turkey":"TUR","Iran":"IRN","Saudi Arabia":"KSA",
    "Qatar":"QAT","Nigeria":"NGA","Ghana":"GHA","Cameroon":"CMR",
    "South Africa":"RSA","Tunisia":"TUN","Algeria":"DZA","Egypt":"EGY",
    "Paraguay":"PAR","Chile":"CHI","Peru":"PER","Bolivia":"BOL","Venezuela":"VEN",
    "Costa Rica":"CRC","Honduras":"HON","Panama":"PAN","Jamaica":"JAM",
    "Haiti":"HAI","Curaçao":"CUW","Uzbekistan":"UZB","Jordan":"JOR",
    "Cape Verde":"CPV","DR Congo":"COD","Iraq":"IRQ","New Zealand":"NZL",
    "Bosnia and Herzegovina":"BIH","Bosnia & Herzegovina":"BIH",
    "Georgia":"GEO","Albania":"ALB","Austria":"AUT","Scotland":"SCO",
    "Norway":"NOR","Sweden":"SWE","Ivory Coast":"CIV",
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def fed(team: str) -> str:
    return FEDERATIONS.get(team, "")

def cc(team: str) -> str:
    return COUNTRY_CODES.get(team, team[:3].upper())

def parse_minute(raw) -> int | str:
    if raw is None:
        return ""
    s = str(raw).strip().rstrip("'′+")
    # Handle "45+2" style
    m = re.match(r"^(\d+)(?:\+(\d+))?", s)
    if not m:
        return s
    return int(m.group(1)) + (int(m.group(2)) if m.group(2) else 0)

def winner(team1: str, team2: str, score: list | None) -> str:
    if not score or len(score) < 2:
        return ""
    g1, g2 = score[0], score[1]
    if g1 > g2: return team1
    if g2 > g1: return team2
    return ""

def score_str(match: dict) -> str:
    ft = (match.get("score") or {}).get("ft")
    if not ft or len(ft) < 2:
        return ""
    s = f"{ft[0]}-{ft[1]}"
    # Check for AET / penalties in the source (not always present)
    if match.get("result") == "aet":
        s += " aet"
    return s

# ── Core converter ─────────────────────────────────────────────────────────────

def match_to_rows(match: dict) -> list[dict]:
    team1 = match.get("team1", "")
    team2 = match.get("team2", "")
    ft    = (match.get("score") or {}).get("ft")
    sc    = score_str(match)
    win   = winner(team1, team2, ft)
    wfed  = fed(win) if win else ""

    # Round label — openfootball uses "Matchday N" for groups and stage names for KO
    rnd_raw = match.get("round", "")
    group   = match.get("group", "")
    rnd     = _round_label(rnd_raw, group)

    # Build goal list sorted by minute
    goals: list[dict] = []
    for g in (match.get("goals1") or []):
        name = g.get("name", "")
        og   = " (OG)"   if g.get("og")  else ""
        pen  = " (pen.)" if g.get("penalty") else ""
        goals.append({"player": name + og + pen, "team": team1, "minute": parse_minute(g.get("minute"))})
    for g in (match.get("goals2") or []):
        name = g.get("name", "")
        og   = " (OG)"   if g.get("og")  else ""
        pen  = " (pen.)" if g.get("penalty") else ""
        goals.append({"player": name + og + pen, "team": team2, "minute": parse_minute(g.get("minute"))})

    goals.sort(key=lambda g: g["minute"] if isinstance(g["minute"], int) else 9999)

    # Cards — openfootball basic JSON doesn't include cards; leave blank
    # (the .more dataset does, but requires more complex parsing)
    yellow_str = ""
    red_str    = ""

    # Build rows
    h = a = 0
    rows: list[dict] = []
    first = True

    for g in goals:
        if g["team"] == team1:
            h += 1
        else:
            a += 1
        rows.append({
            "Year": YEAR, "Host": HOST, "Round": rnd,
            "Team":               team1 if first else "",
            "Team__1":            team2 if first else "",
            "Final Score":        sc    if first else "",
            "Winnning Team":      win   if first else "",
            "Winning Federation": wfed  if first else "",
            "Scorers":            f"{g['player']} ({cc(g['team'])})",
            "Time scored":        g["minute"],
            "Progess Score":      f"{h}-{a}",
            "Yellow Cards":       yellow_str if first else "",
            "Red Cards":          red_str    if first else "",
            "Referee":            ""         if first else "",
        })
        first = False

    # No goals yet (0-0 or unplayed): emit one header row
    if not rows:
        rows = [{
            "Year": YEAR, "Host": HOST, "Round": rnd,
            "Team": team1, "Team__1": team2,
            "Final Score": sc, "Winnning Team": win,
            "Winning Federation": wfed,
            "Scorers": "", "Time scored": "", "Progess Score": "",
            "Yellow Cards": "", "Red Cards": "", "Referee": "",
        }]

    return rows


def _round_label(rnd: str, group: str) -> str:
    # openfootball uses "Matchday 1/2/3" for group stage
    if re.match(r"Matchday \d", rnd, re.I):
        return group if group else rnd
    # Knockout stage labels
    mapping = {
        "Round of 32":    "Round of 32",
        "Round of 16":    "Round of 16",
        "Quarterfinal":   "Quarter-final",
        "Quarter-final":  "Quarter-final",
        "Semifinal":      "Semi-final",
        "Semi-final":     "Semi-final",
        "Third place":    "Third place",
        "Final":          "Final",
    }
    return mapping.get(rnd, rnd)


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
    print("FIFA World Cup 2026 — openfootball/worldcup.json")
    print("=" * 60)
    print(f"\nSource: {SOURCE_URL}\n")

    r = requests.get(SOURCE_URL, timeout=15,
                     headers={"User-Agent": "worldcup-data-fetcher/1.0"})
    r.raise_for_status()
    source = r.json()

    matches = source.get("matches", [])
    print(f"Found {len(matches)} matches in source")

    # Only process matches that have a score (played)
    played = [m for m in matches if (m.get("score") or {}).get("ft")]
    print(f"{len(played)} with scores, {len(matches)-len(played)} upcoming\n")

    all_new_rows: list[dict] = []
    for m in played:
        rows = match_to_rows(m)
        all_new_rows.extend(rows)
        goals = sum(1 for r in rows if r["Scorers"])
        print(f"  {m['team1']} {(m.get('score') or {}).get('ft','?')} {m['team2']}"
              f"  ({rows[0]['Round']})  → {goals} goal(s)")

    print(f"\nMerging with existing data in {DATA_FILE}…")
    existing = load_existing()
    merged   = merge(existing, all_new_rows)
    save(merged)

    total_goals = sum(1 for r in all_new_rows if r["Scorers"])
    print(f"2026 matches: {len(played)}  |  goal rows: {total_goals}")


if __name__ == "__main__":
    main()
