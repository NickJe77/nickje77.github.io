#!/usr/bin/env python3
"""
Rugby Union Results Scraper (fast - results only, no player stats)

Scans ESPN scoreboard by date for match results only.
Run this first to build the match database, then run
rugby_player_scraper.py separately for player stats.

Usage:
  python scripts/rugby_results_scraper.py 2020 2026
"""

import requests
import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

SITE  = "https://site.api.espn.com/apis/site/v2/sports/rugby"
DATA  = Path("docs/data/rugby")
DATA.mkdir(parents=True, exist_ok=True)

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2020
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

COMPETITIONS = [
    {"id": "164205", "name": "Rugby World Cup",              "start": 1987, "months": [(9,11)], "wc_years": {1987,1991,1995,1999,2003,2007,2011,2015,2019,2023}},
    {"id": "180659", "name": "Six Nations",                  "start": 1978, "months": [(1,3)]},
    {"id": "244293", "name": "The Rugby Championship",       "start": 1996, "months": [(7,10)]},
    {"id": "242041", "name": "Super Rugby Pacific",          "start": 1996, "months": [(2,7)]},
    {"id": "267979", "name": "Gallagher Premiership",        "start": 1998, "months": [(9,12),(1,6)]},
    {"id": "270557", "name": "United Rugby Championship",    "start": 2008, "months": [(9,12),(1,6)]},
    {"id": "271937", "name": "European Rugby Champions Cup", "start": 2008, "months": [(10,12),(1,5)]},
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

def dates_for_year(comp, year):
    wc_years = comp.get("wc_years")
    if wc_years and year not in wc_years:
        return []
    dates = []
    for m_start, m_end in comp.get("months", []):
        if m_start <= m_end:
            d = datetime(year, m_start, 1)
            # Last day of m_end
            if m_end == 12:
                end = datetime(year, 12, 31)
            else:
                end = datetime(year, m_end+1, 1) - timedelta(days=1)
        else:
            d = datetime(year, m_start, 1)
            end = datetime(year+1, m_end+1, 1) - timedelta(days=1)
        while d <= end:
            dates.append(d.strftime("%Y%m%d"))
            d += timedelta(days=1)
    return dates

def scoreboard_matches(league_id, date_str):
    data = get(f"{SITE}/{league_id}/scoreboard?dates={date_str}&lang=en&region=us")
    if not data:
        return []
    matches = []
    for event in data.get("events", []):
        comps = event.get("competitions", [])
        if not comps:
            continue
        comp    = comps[0]
        comp_id = str(comp.get("id", event.get("id","")))
        event_id= str(event.get("id",""))
        if not comp.get("status",{}).get("type",{}).get("completed", False):
            continue
        competitors = comp.get("competitors",[])
        if len(competitors) < 2:
            continue
        home = next((c for c in competitors if c.get("homeAway")=="home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway")=="away"), competitors[1])
        matches.append({
            "id":         event_id,
            "comp_id":    comp_id,
            "date":       date_str[:4]+"-"+date_str[4:6]+"-"+date_str[6:],
            "name":       event.get("name",""),
            "home_team":  (home.get("team") or {}).get("displayName",""),
            "away_team":  (away.get("team") or {}).get("displayName",""),
            "home_abbr":  (home.get("team") or {}).get("abbreviation",""),
            "away_abbr":  (away.get("team") or {}).get("abbreviation",""),
            "home_id":    str(home.get("id","")),
            "away_id":    str(away.get("id","")),
            "home_score": home.get("score",""),
            "away_score": away.get("score",""),
            "winner":     (home.get("team") or {}).get("displayName","") if home.get("winner") else (away.get("team") or {}).get("displayName","") if away.get("winner") else "",
            "venue":      (comp.get("venue") or {}).get("fullName",""),
        })
    return matches

DATA.joinpath("index.json").write_text(json.dumps(
    [{k:v for k,v in c.items() if k not in ("months","wc_years")} for c in COMPETITIONS],
    separators=(",",":")
))

for comp in COMPETITIONS:
    lid  = comp["id"]
    name = comp["name"]
    ldir = DATA / lid
    ldir.mkdir(exist_ok=True)

    y_start = max(START_YEAR, comp["start"])
    print(f"\n{name} ({lid})")

    season_index = []
    # Load existing season index
    idx_file = ldir / "index.json"
    if idx_file.exists():
        try: season_index = json.loads(idx_file.read_text())
        except: pass
    existing_years = {s["year"] for s in season_index}

    for year in range(y_start, END_YEAR + 1):
        out = ldir / f"{year}.json"
        existing = []
        existing_ids = set()
        if out.exists():
            try:
                existing = json.loads(out.read_text())
                existing_ids = set(m["id"] for m in existing)
            except: pass

        dates = dates_for_year(comp, year)
        if not dates:
            continue

        new_matches = []
        for date_str in dates:
            for m in scoreboard_matches(lid, date_str):
                if m["id"] not in existing_ids:
                    existing_ids.add(m["id"])
                    save = {k:v for k,v in m.items() if k != "comp_id"}
                    new_matches.append(save)
                    print(f"  {m['date']}: {m['home_team']} {m['home_score']} - {m['away_score']} {m['away_team']}")
            time.sleep(0.15)

        all_matches = sorted(existing + new_matches, key=lambda m: m.get("date",""))
        if all_matches:
            out.write_text(json.dumps(all_matches, indent=2))
            if year not in existing_years:
                season_index.append({"year": year, "matches": len(all_matches)})
                existing_years.add(year)
            else:
                for s in season_index:
                    if s["year"] == year:
                        s["matches"] = len(all_matches)
            print(f"  {year}: {len(all_matches)} matches total")

    season_index.sort(key=lambda s: s["year"])
    idx_file.write_text(json.dumps(season_index, separators=(",",":")))

print("\nDONE")
