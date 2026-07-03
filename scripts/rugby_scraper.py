#!/usr/bin/env python3
"""
Rugby Union Data Scraper — full version with match results AND player stats.

Uses core ESPN API for match results (reliable for historical data)
and roster/statistics endpoints for player stats.

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

BASE  = "https://sports.core.api.espn.com/v2/sports/rugby"
DATA  = Path("docs/data/rugby")
DATA.mkdir(parents=True, exist_ok=True)
PLAYERS_DIR   = DATA / "players"
PLAYERS_DIR.mkdir(exist_ok=True)
PLAYERS_INDEX = DATA / "players.json"

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 1978
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

COMPETITIONS = [
    {"id": "164205", "name": "Rugby World Cup",              "start": 1987},
    {"id": "180659", "name": "Six Nations",                  "start": 1978},
    {"id": "244293", "name": "The Rugby Championship",       "start": 1996},
    {"id": "242041", "name": "Super Rugby Pacific",          "start": 1996},
    {"id": "267979", "name": "Gallagher Premiership",        "start": 1998},
    {"id": "270557", "name": "United Rugby Championship",    "start": 2008},
    {"id": "271937", "name": "European Rugby Champions Cup", "start": 2008},
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

def resolve(obj):
    """If obj is a ref dict, fetch it. Otherwise return as-is."""
    if isinstance(obj, dict) and "$ref" in obj and len(obj) <= 2:
        return get(obj["$ref"]) or obj
    return obj

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
        "name":     data.get("fullName", ""),
        "position": pos.get("displayName", "") if isinstance(pos, dict) else "",
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
    for cat in data.get("splits", {}).get("categories", []):
        for s in cat.get("stats", []):
            stats[s["name"]] = s.get("value", 0)
    return stats

def fetch_event_ids(league_id, year):
    data = get(f"{BASE}/leagues/{league_id}/seasons/{year}/events?limit=200&lang=en&region=us")
    if not data:
        return []
    ids = []
    for item in data.get("items", []):
        ref = item.get("$ref", "")
        eid = ref.split("/events/")[-1].split("?")[0] if "/events/" in ref else str(item.get("id",""))
        if eid:
            ids.append(eid)
    return ids

def fetch_match_and_players(league_id, event_id):
    """Fetch match result and player stats using core API."""
    data = get(f"{BASE}/leagues/{league_id}/events/{event_id}?lang=en&region=us")
    if not data:
        return None, []

    date  = (data.get("date","") or "")[:10]
    name  = data.get("name","")
    comps = data.get("competitions", [])
    if not comps:
        return None, []

    comp    = resolve(comps[0])
    comp_id = comp.get("id", event_id)

    # Status
    status = resolve(comp.get("status", {}))
    completed = (status.get("type") or {}).get("completed", False)
    if not completed:
        return None, []

    # Competitors
    raw_competitors = comp.get("competitors", [])
    results = []
    for rc in raw_competitors:
        c = resolve(rc)
        team = resolve(c.get("team", {}))
        score = c.get("score", "")
        if isinstance(score, dict):
            score_data = resolve(score)
            score = score_data.get("value", "")
        results.append({
            "team":      team.get("displayName",""),
            "abbr":      team.get("abbreviation",""),
            "team_id":   str(c.get("id","")),
            "score":     score,
            "winner":    c.get("winner", False),
            "home_away": c.get("homeAway",""),
        })
        time.sleep(0.05)

    if len(results) < 2:
        return None, []

    home = next((r for r in results if r["home_away"]=="home"), results[0])
    away = next((r for r in results if r["home_away"]=="away"), results[1])

    venues = data.get("venues",[])
    venue = ""
    if venues:
        v = resolve(venues[0])
        venue = v.get("fullName","") or v.get("name","")

    match = {
        "id":         str(event_id),
        "name":       name,
        "date":       date,
        "home_team":  home["team"],
        "away_team":  away["team"],
        "home_abbr":  home["abbr"],
        "away_abbr":  away["abbr"],
        "home_id":    home["team_id"],
        "away_id":    away["team_id"],
        "home_score": home["score"],
        "away_score": away["score"],
        "winner":     home["team"] if home["winner"] else (away["team"] if away["winner"] else ""),
        "venue":      venue,
    }

    # Player stats
    player_logs = []
    for side in results:
        team_id   = side["team_id"]
        team_name = side["team"]
        opp_name  = away["team"] if team_id == home["team_id"] else home["team"]

        roster_data = get(f"{BASE}/leagues/{league_id}/events/{event_id}/competitions/{comp_id}/competitors/{team_id}/roster?lang=en&region=us")
        if not roster_data:
            continue

        for entry in roster_data.get("entries", []):
            pid = str(entry.get("playerId",""))
            if not pid:
                continue

            athlete = fetch_athlete(pid)
            stats   = fetch_player_stats(league_id, event_id, comp_id, team_id, pid)

            log = {
                "event_id":          str(event_id),
                "date":              date,
                "competition":       league_id,
                "team":              team_name,
                "opponent":          opp_name,
                "home_away":         "home" if team_id == home["team_id"] else "away",
                "starter":           entry.get("starter", False),
                "jersey":            entry.get("jersey",""),
                "tries":             int(stats.get("tries",0) or 0),
                "points":            int(stats.get("points",0) or 0),
                "tackles":           int(stats.get("tackles",0) or 0),
                "missed_tackles":    int(stats.get("missedTackles",0) or 0),
                "metres":            int(stats.get("metres",0) or 0),
                "runs":              int(stats.get("runs",0) or 0),
                "clean_breaks":      int(stats.get("cleanBreaks",0) or 0),
                "defenders_beaten":  int(stats.get("defendersBeaten",0) or 0),
                "passes":            int(stats.get("passes",0) or 0),
                "kicks":             int(stats.get("kicks",0) or 0),
                "kick_metres":       int(stats.get("kickFromHandMetres",0) or 0),
                "penalties":         int(stats.get("penaltiesConceded",0) or 0),
                "yellow_cards":      int(stats.get("yellowCards",0) or 0),
                "red_cards":         int(stats.get("redCards",0) or 0),
                "minutes":           int(stats.get("minutesPlayedTotal",0) or 0),
                "try_assists":       int(stats.get("tryAssists",0) or 0),
                "offloads":          int(stats.get("offload",0) or 0),
                "turnovers":         int(stats.get("turnoversConceded",0) or 0),
                "penalty_goals":     int(stats.get("penaltyGoals",0) or 0),
                "conversions":       int(stats.get("conversionGoals",0) or 0),
                "drop_goals":        int(stats.get("dropGoalsConverted",0) or 0),
            }
            player_logs.append((pid, athlete, log))
            time.sleep(0.1)

    return match, player_logs

# ── Main loop ────────────────────────────────────────────────────────────────

DATA.joinpath("index.json").write_text(json.dumps(COMPETITIONS, separators=(",",":")))

for comp in COMPETITIONS:
    lid  = comp["id"]
    name = comp["name"]
    ldir = DATA / lid
    ldir.mkdir(exist_ok=True)

    y_start = min(START_YEAR, comp["start"])
    print(f"\n{'='*50}\n{name} ({lid}) from {y_start}")

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

        eids = fetch_event_ids(lid, year)
        if not eids:
            continue

        new_ids = [e for e in eids if e not in existing_ids]
        if not new_ids:
            print(f"  {year}: {len(existing)} already saved")
            if existing: season_index.append({"year": year, "matches": len(existing)})
            continue

        print(f"  {year}: fetching {len(new_ids)} new matches")
        new_matches = []

        for i, eid in enumerate(new_ids):
            m, player_logs = fetch_match_and_players(lid, eid)
            if m:
                new_matches.append(m)
                print(f"    [{i+1}/{len(new_ids)}] {m['home_team']} {m['home_score']} - {m['away_score']} {m['away_team']} ({len(player_logs)} players)")

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
                    if str(eid) not in set(g["event_id"] for g in plog):
                        plog.append(log)
                        pfile.write_text(json.dumps(plog, separators=(",",":")))
            else:
                print(f"    [{i+1}/{len(new_ids)}] {eid} — no result yet")
            time.sleep(0.3)

        all_matches = sorted(existing + new_matches, key=lambda m: m.get("date",""))
        if all_matches:
            out.write_text(json.dumps(all_matches, indent=2))
            season_index.append({"year": year, "matches": len(all_matches)})
            print(f"  {year}: saved {len(all_matches)} matches")

        # Save player index after each season
        idx = sorted(players_index.values(), key=lambda p: p.get("name",""))
        PLAYERS_INDEX.write_text(json.dumps(idx, separators=(",",":")))

    ldir.joinpath("index.json").write_text(json.dumps(season_index, separators=(",",":")))

idx = sorted(players_index.values(), key=lambda p: p.get("name",""))
PLAYERS_INDEX.write_text(json.dumps(idx, separators=(",",":")))
print(f"\nDONE — {len(idx)} players")
