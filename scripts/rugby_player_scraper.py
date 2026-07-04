#!/usr/bin/env python3
"""
Rugby Union Player Stats Scraper

Reads already-saved match result files and fetches player stats
for each match from the ESPN API.

Run after rugby_results_scraper.py has built the match files.

Output:
  docs/data/rugby/players.json
  docs/data/rugby/players/{id}.json

Usage:
  python scripts/rugby_player_scraper.py 2020 2026
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE  = "https://sports.core.api.espn.com/v2/sports/rugby"
DATA  = Path("docs/data/rugby")
PLAYERS_DIR   = DATA / "players"
PLAYERS_DIR.mkdir(parents=True, exist_ok=True)
PLAYERS_INDEX = DATA / "players.json"

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2020
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

COMPETITIONS = [
    "164205", "180659", "244293", "242041", "267979", "270557", "271937"
]

players_index = {}
if PLAYERS_INDEX.exists():
    for p in json.loads(PLAYERS_INDEX.read_text()):
        players_index[p["id"]] = p

athlete_cache = {}

# Track which match IDs have already had player stats processed
processed_matches = set()
for f in PLAYERS_DIR.glob("*.json"):
    try:
        logs = json.loads(f.read_text())
        for log in logs:
            processed_matches.add(log.get("event_id",""))
    except:
        pass
print(f"Already processed: {len(processed_matches)} match entries")

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

def get_comp_id(league_id, event_id):
    """Get competition ID — usually same as event ID for rugby."""
    data = get(f"{BASE}/leagues/{league_id}/events/{event_id}?lang=en&region=us")
    if not data:
        return str(event_id)
    comps = data.get("competitions",[])
    if comps:
        c = comps[0]
        if isinstance(c, dict) and "$ref" not in c:
            return str(c.get("id", event_id))
        elif isinstance(c, dict) and "$ref" in c:
            cd = get(c["$ref"]) or {}
            return str(cd.get("id", event_id))
    return str(event_id)

def fetch_players_for_match(league_id, event_id, comp_id, home_id, away_id, home_name, away_name, date):
    logs = []
    for team_id, team_name, opp_name in [(home_id, home_name, away_name), (away_id, away_name, home_name)]:
        if not team_id:
            continue
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

# ── Main loop ────────────────────────────────────────────────────────────────

for lid in COMPETITIONS:
    ldir = DATA / lid
    if not ldir.exists():
        continue

    print(f"\n{'='*50}\nLeague {lid}")

    for year in range(START_YEAR, END_YEAR + 1):
        match_file = ldir / f"{year}.json"
        if not match_file.exists():
            continue

        try:
            matches = json.loads(match_file.read_text())
        except:
            continue

        new_matches = [m for m in matches if str(m.get("id","")) not in processed_matches]
        if not new_matches:
            print(f"  {year}: all matches already processed")
            continue

        print(f"  {year}: {len(new_matches)} matches to process")

        for i, m in enumerate(new_matches):
            eid     = str(m.get("id",""))
            comp_id = get_comp_id(lid, eid)

            player_logs = fetch_players_for_match(
                lid, eid, comp_id,
                m.get("home_id",""), m.get("away_id",""),
                m.get("home_team",""), m.get("away_team",""),
                m.get("date","")
            )

            print(f"    [{i+1}/{len(new_matches)}] {m.get('home_team')} v {m.get('away_team')} — {len(player_logs)} players")

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
                plog  = []
                if pfile.exists():
                    try: plog = json.loads(pfile.read_text())
                    except: pass
                if eid not in set(g["event_id"] for g in plog):
                    plog.append(log)
                    pfile.write_text(json.dumps(plog, separators=(",",":")))

            processed_matches.add(eid)
            time.sleep(0.3)

        # Save index after each season
        idx = sorted(players_index.values(), key=lambda p: p.get("name",""))
        PLAYERS_INDEX.write_text(json.dumps(idx, separators=(",",":")))
        print(f"  {year}: done — {len(players_index)} players indexed")

idx = sorted(players_index.values(), key=lambda p: p.get("name",""))
PLAYERS_INDEX.write_text(json.dumps(idx, separators=(",",":")))
print(f"\nDONE — {len(idx)} players")
