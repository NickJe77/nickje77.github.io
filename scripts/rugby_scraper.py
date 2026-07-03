#!/usr/bin/env python3
"""
Rugby Union Data Scraper

Scans the ESPN scoreboard by date to find matches for each competition.
Uses the site scoreboard API which reliably returns historical results.

Output:
  docs/data/rugby/index.json
  docs/data/rugby/{league_id}/index.json
  docs/data/rugby/{league_id}/{year}.json
  docs/data/rugby/players.json
  docs/data/rugby/players/{id}.json

Usage:
  python scripts/rugby_scraper.py
  python scripts/rugby_scraper.py 2020 2026
"""

import requests
import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

SITE  = "https://site.api.espn.com/apis/site/v2/sports/rugby"
BASE  = "https://sports.core.api.espn.com/v2/sports/rugby"
DATA  = Path("docs/data/rugby")
DATA.mkdir(parents=True, exist_ok=True)
PLAYERS_DIR   = DATA / "players"
PLAYERS_DIR.mkdir(exist_ok=True)
PLAYERS_INDEX = DATA / "players.json"

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 1978
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

COMPETITIONS = [
    {
        "id": "164205", "name": "Rugby World Cup", "start": 1987,
        "months": [(9,11)],  # Sep-Nov, only World Cup years
        "wc_years": {1987,1991,1995,1999,2003,2007,2011,2015,2019,2023}
    },
    {
        "id": "180659", "name": "Six Nations", "start": 1978,
        "months": [(1,3)]   # Jan-Mar
    },
    {
        "id": "244293", "name": "The Rugby Championship", "start": 1996,
        "months": [(7,10)]  # Jul-Oct
    },
    {
        "id": "242041", "name": "Super Rugby Pacific", "start": 1996,
        "months": [(2,7)]   # Feb-Jul
    },
    {
        "id": "267979", "name": "Gallagher Premiership", "start": 1998,
        "months": [(9,12),(1,6)]  # Sep-Dec and Jan-Jun
    },
    {
        "id": "270557", "name": "United Rugby Championship", "start": 2008,
        "months": [(9,12),(1,6)]
    },
    {
        "id": "271937", "name": "European Rugby Champions Cup", "start": 2008,
        "months": [(10,12),(1,5)]
    },
]

players_index = {}
if PLAYERS_INDEX.exists():
    for p in json.loads(PLAYERS_INDEX.read_text()):
        players_index[p["id"]] = p

athlete_cache = {}

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

def fetch_athlete(pid):
    pid = str(pid)
    if pid in athlete_cache:
        return athlete_cache[pid]
    data = get(f"{BASE}/athletes/{pid}?lang=en&region=us")
    if not data:
        return {}
    pos = data.get("position", {})
    if isinstance(pos, dict) and "$ref" in pos:
        pos = get(pos["$ref"]) or {}
    info = {
        "id":       pid,
        "name":     data.get("fullName",""),
        "position": pos.get("displayName","") if isinstance(pos,dict) else "",
        "dob":      (data.get("dateOfBirth","") or "")[:10],
        "height":   data.get("displayHeight",""),
        "weight":   data.get("displayWeight",""),
        "slug":     data.get("slug",""),
    }
    athlete_cache[pid] = info
    time.sleep(0.1)
    return info

def fetch_player_stats(league_id, event_id, comp_id, team_id, player_id):
    url = f"{BASE}/leagues/{league_id}/events/{event_id}/competitions/{comp_id}/competitors/{team_id}/roster/{player_id}/statistics/0?lang=en&region=us"
    data = get(url)
    if not data:
        return {}
    stats = {}
    for cat in data.get("splits",{}).get("categories",[]):
        for s in cat.get("stats",[]):
            stats[s["name"]] = s.get("value",0)
    return stats

def fetch_players_for_match(league_id, event_id, comp_id, home_id, away_id, home_name, away_name, date):
    logs = []
    for team_id, team_name, opp_name in [(home_id, home_name, away_name), (away_id, away_name, home_name)]:
        roster = get(f"{BASE}/leagues/{league_id}/events/{event_id}/competitions/{comp_id}/competitors/{team_id}/roster?lang=en&region=us")
        if not roster:
            continue
        for entry in roster.get("entries",[]):
            pid = str(entry.get("playerId",""))
            if not pid:
                continue
            athlete = fetch_athlete(pid)
            stats   = fetch_player_stats(league_id, event_id, comp_id, team_id, pid)
            log = {
                "event_id":        str(event_id),
                "date":            date,
                "competition":     league_id,
                "team":            team_name,
                "opponent":        opp_name,
                "home_away":       "home" if team_id==home_id else "away",
                "starter":         entry.get("starter",False),
                "jersey":          entry.get("jersey",""),
                "tries":           int(stats.get("tries",0) or 0),
                "points":          int(stats.get("points",0) or 0),
                "tackles":         int(stats.get("tackles",0) or 0),
                "missed_tackles":  int(stats.get("missedTackles",0) or 0),
                "metres":          int(stats.get("metres",0) or 0),
                "runs":            int(stats.get("runs",0) or 0),
                "clean_breaks":    int(stats.get("cleanBreaks",0) or 0),
                "defenders_beaten":int(stats.get("defendersBeaten",0) or 0),
                "passes":          int(stats.get("passes",0) or 0),
                "kicks":           int(stats.get("kicks",0) or 0),
                "kick_metres":     int(stats.get("kickFromHandMetres",0) or 0),
                "penalties":       int(stats.get("penaltiesConceded",0) or 0),
                "yellow_cards":    int(stats.get("yellowCards",0) or 0),
                "red_cards":       int(stats.get("redCards",0) or 0),
                "minutes":         int(stats.get("minutesPlayedTotal",0) or 0),
                "try_assists":     int(stats.get("tryAssists",0) or 0),
                "offloads":        int(stats.get("offload",0) or 0),
                "turnovers":       int(stats.get("turnoversConceded",0) or 0),
                "penalty_goals":   int(stats.get("penaltyGoals",0) or 0),
                "conversions":     int(stats.get("conversionGoals",0) or 0),
                "drop_goals":      int(stats.get("dropGoalsConverted",0) or 0),
            }
            logs.append((pid, athlete, log))
            time.sleep(0.1)
    return logs

def date_range_for_year(comp, year):
    """Generate list of dates to scan for this competition in this year."""
    wc_years = comp.get("wc_years")
    if wc_years and year not in wc_years:
        return []

    dates = []
    for month_range in comp.get("months", []):
        start_m, end_m = month_range
        if start_m <= end_m:
            # Same year
            d = datetime(year, start_m, 1)
            end = datetime(year, end_m, 28) + timedelta(days=4)
            end = end.replace(day=1) - timedelta(days=1)  # last day of month
        else:
            # Wraps year — shouldn't happen with our config
            d = datetime(year, start_m, 1)
            end = datetime(year+1, end_m, 28)

        while d <= end:
            dates.append(d.strftime("%Y%m%d"))
            d += timedelta(days=1)
    return dates

def scoreboard_matches(league_id, date_str):
    """Fetch all completed matches for a league on a given date."""
    data = get(f"{SITE}/{league_id}/scoreboard?dates={date_str}&lang=en&region=us")
    if not data:
        return []

    matches = []
    for event in data.get("events", []):
        comps = event.get("competitions", [])
        if not comps:
            continue
        comp     = comps[0]
        comp_id  = str(comp.get("id", event.get("id","")))
        event_id = str(event.get("id",""))
        status   = comp.get("status",{})
        if not status.get("type",{}).get("completed", False):
            continue

        competitors = comp.get("competitors",[])
        if len(competitors) < 2:
            continue

        home = next((c for c in competitors if c.get("homeAway")=="home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway")=="away"), competitors[1])

        venue = (comp.get("venue") or {}).get("fullName","")

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
            "venue":      venue,
        })
    return matches

# ── Main loop ────────────────────────────────────────────────────────────────

DATA.joinpath("index.json").write_text(json.dumps(
    [{k:v for k,v in c.items() if k not in ("months","wc_years")} for c in COMPETITIONS],
    separators=(",",":")
))

for comp in COMPETITIONS:
    lid   = comp["id"]
    name  = comp["name"]
    ldir  = DATA / lid
    ldir.mkdir(exist_ok=True)

    y_start = min(START_YEAR, comp["start"])
    print(f"\n{'='*50}\n{name} ({lid})")

    season_index = []

    for year in range(y_start, END_YEAR + 1):
        out = ldir / f"{year}.json"
        existing = []
        existing_ids = set()
        if out.exists():
            try:
                existing = json.loads(out.read_text())
                existing_ids = set(m["id"] for m in existing)
            except: pass

        dates = date_range_for_year(comp, year)
        if not dates:
            continue

        new_matches = []
        for date_str in dates:
            day_matches = scoreboard_matches(lid, date_str)
            for m in day_matches:
                if m["id"] in existing_ids:
                    continue
                existing_ids.add(m["id"])

                # Fetch player stats
                player_logs = fetch_players_for_match(
                    lid, m["id"], m["comp_id"],
                    m["home_id"], m["away_id"],
                    m["home_team"], m["away_team"],
                    m["date"]
                )

                # Save player data
                for pid, athlete, log in player_logs:
                    if pid not in players_index:
                        players_index[pid] = {
                            "id": pid, "name": athlete.get("name",pid),
                            "position": athlete.get("position",""),
                            "dob": athlete.get("dob",""),
                            "height": athlete.get("height",""),
                            "weight": athlete.get("weight",""),
                            "slug": athlete.get("slug",""),
                            "competitions": [],
                        }
                    if lid not in players_index[pid]["competitions"]:
                        players_index[pid]["competitions"].append(lid)

                    pfile = PLAYERS_DIR / f"{pid}.json"
                    plog = []
                    if pfile.exists():
                        try: plog = json.loads(pfile.read_text())
                        except: pass
                    if str(m["id"]) not in set(g["event_id"] for g in plog):
                        plog.append(log)
                        pfile.write_text(json.dumps(plog, separators=(",",":")))

                # Strip comp_id before saving match
                save_m = {k:v for k,v in m.items() if k != "comp_id"}
                new_matches.append(save_m)
                print(f"  {year} {m['date']}: {m['home_team']} {m['home_score']} - {m['away_score']} {m['away_team']} ({len(player_logs)} players)")

            time.sleep(0.2)

        all_matches = sorted(existing + new_matches, key=lambda m: m.get("date",""))
        if all_matches:
            out.write_text(json.dumps(all_matches, indent=2))
            season_index.append({"year": year, "matches": len(all_matches)})

        if new_matches:
            idx = sorted(players_index.values(), key=lambda p: p.get("name",""))
            PLAYERS_INDEX.write_text(json.dumps(idx, separators=(",",":")))

    ldir.joinpath("index.json").write_text(json.dumps(season_index, separators=(",",":")))
    print(f"  {name}: {sum(s['matches'] for s in season_index)} total matches across {len(season_index)} seasons")

idx = sorted(players_index.values(), key=lambda p: p.get("name",""))
PLAYERS_INDEX.write_text(json.dumps(idx, separators=(",",":")))
print(f"\nDONE — {len(idx)} players")
