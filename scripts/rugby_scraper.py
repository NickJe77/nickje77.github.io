#!/usr/bin/env python3
"""
Rugby Union Data Scraper

Fetches match results from the ESPN API for major Rugby Union competitions.

Competitions:
  164205 — Rugby World Cup
  180659 — Six Nations
  244293 — The Rugby Championship
  242041 — Super Rugby Pacific
  267979 — Gallagher Premiership
  270557 — United Rugby Championship
  271937 — European Rugby Champions Cup

Output:
  docs/data/rugby/index.json                        — all competitions
  docs/data/rugby/{competition_id}/index.json       — seasons for competition
  docs/data/rugby/{competition_id}/{year}.json      — matches for season

Usage:
  python scripts/rugby_scraper.py
  python scripts/rugby_scraper.py 2020 2026
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE     = "https://sports.core.api.espn.com/v2/sports/rugby/leagues"
SITE     = "https://site.api.espn.com/apis/site/v2/sports/rugby"
DATA_DIR = Path("docs/data/rugby")
DATA_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

COMPETITIONS = [
    {"id": "164205", "name": "Rugby World Cup",                "slug": "world-cup"},
    {"id": "180659", "name": "Six Nations",                    "slug": "six-nations"},
    {"id": "244293", "name": "The Rugby Championship",         "slug": "rugby-championship"},
    {"id": "242041", "name": "Super Rugby Pacific",            "slug": "super-rugby-pacific"},
    {"id": "267979", "name": "Gallagher Premiership",          "slug": "premiership"},
    {"id": "270557", "name": "United Rugby Championship",      "slug": "urc"},
    {"id": "271937", "name": "European Rugby Champions Cup",   "slug": "champions-cup"},
]

def get(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=30)
            if r.ok:
                return r.json()
            time.sleep(1)
        except Exception as e:
            print(f"  WARN: {e}")
            time.sleep(2)
    return {}

def fetch_match(league_id, event_id):
    """Fetch match result using the summary endpoint — one call gets everything."""
    data = get(f"{SITE}/{league_id}/summary?event={event_id}")
    if not data:
        return None

    header = data.get("header", {})
    comps  = header.get("competitions", [])
    if not comps:
        return None

    comp        = comps[0]
    status      = comp.get("status", {})
    status_type = status.get("type", {})
    completed   = status_type.get("completed", False)

    if not completed:
        return None

    competitors = comp.get("competitors", [])
    if len(competitors) < 2:
        return None

    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

    home_team  = (home.get("team") or {}).get("displayName", "")
    away_team  = (away.get("team") or {}).get("displayName", "")
    home_abbr  = (home.get("team") or {}).get("abbreviation", "")
    away_abbr  = (away.get("team") or {}).get("abbreviation", "")
    home_score = home.get("score", "")
    away_score = away.get("score", "")
    home_winner= home.get("winner", False)

    # Venue
    game_info = data.get("gameInfo", {})
    venue     = (game_info.get("venue") or {}).get("fullName", "")

    return {
        "id":         event_id,
        "date":       comp.get("date", "")[:10],
        "home_team":  home_team,
        "away_team":  away_team,
        "home_abbr":  home_abbr,
        "away_abbr":  away_abbr,
        "home_score": home_score,
        "away_score": away_score,
        "winner":     home_team if home_winner else away_team,
        "venue":      venue,
        "completed":  completed,
    }

def fetch_season_events(league_id, year):
    """Get all event IDs for a competition season."""
    data = get(f"{BASE}/{league_id}/seasons/{year}/events?limit=200&lang=en&region=us")
    if not data:
        return []
    items = data.get("items", [])
    event_ids = []
    for item in items:
        ref = item.get("$ref", "")
        eid = ref.split("/events/")[-1].split("?")[0] if "/events/" in ref else item.get("id","")
        if eid:
            event_ids.append(str(eid))
    return event_ids

# ── Main loop ────────────────────────────────────────────────────────────────

# Save competitions index
DATA_DIR.joinpath("index.json").write_text(json.dumps(COMPETITIONS, separators=(",",":")))

for comp in COMPETITIONS:
    league_id   = comp["id"]
    league_name = comp["name"]
    league_dir  = DATA_DIR / league_id
    league_dir.mkdir(exist_ok=True)

    print(f"\n{'='*50}")
    print(f"{league_name} ({league_id})")

    season_index = []

    for year in range(START_YEAR, END_YEAR + 1):
        out_file = league_dir / f"{year}.json"

        # Load existing
        existing = []
        existing_ids = set()
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text())
                existing_ids = set(m["id"] for m in existing)
            except:
                pass

        print(f"  {year}: fetching event list...")
        event_ids = fetch_season_events(league_id, year)

        if not event_ids:
            print(f"  {year}: no events found")
            continue

        new_ids = [eid for eid in event_ids if eid not in existing_ids]
        print(f"  {year}: {len(event_ids)} events, {len(new_ids)} new")

        new_matches = []
        for i, eid in enumerate(new_ids):
            match = fetch_match(league_id, eid)
            if match:
                new_matches.append(match)
            time.sleep(0.2)

        all_matches = sorted(existing + new_matches, key=lambda m: m.get("date",""))

        if all_matches:
            out_file.write_text(json.dumps(all_matches, indent=2))
            season_index.append({
                "year":    year,
                "matches": len(all_matches),
            })
            print(f"  {year}: saved {len(all_matches)} matches")

        time.sleep(0.3)

    # Save competition season index
    league_dir.joinpath("index.json").write_text(json.dumps(season_index, separators=(",",":")))

print("\nDONE")
