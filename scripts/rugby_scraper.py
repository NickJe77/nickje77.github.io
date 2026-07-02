#!/usr/bin/env python3
"""
Rugby Union Data Scraper

Fetches match results AND player stats from the ESPN API.

Competitions:
  164205 — Rugby World Cup      (from 1987)
  180659 — Six Nations          (from 1978)
  244293 — The Rugby Championship (from 1996)
  242041 — Super Rugby Pacific  (from 1996)
  267979 — Gallagher Premiership (from 1998)
  270557 — United Rugby Championship (from 2008)
  271937 — European Rugby Champions Cup (from 2008)

Output:
  docs/data/rugby/index.json
  docs/data/rugby/{league_id}/{year}.json        — match results
  docs/data/rugby/players.json                   — player index
  docs/data/rugby/players/{id}.json              — player match log

Usage:
  python scripts/rugby_scraper.py
  python scripts/rugby_scraper.py 2020 2026
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE     = "https://sports.core.api.espn.com/v2/sports/rugby"
SITE     = "https://site.api.espn.com/apis/site/v2/sports/rugby"
DATA_DIR = Path("docs/data/rugby")
DATA_DIR.mkdir(parents=True, exist_ok=True)

PLAYERS_DIR  = DATA_DIR / "players"
PLAYERS_DIR.mkdir(exist_ok=True)
PLAYERS_INDEX = DATA_DIR / "players.json"

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 1978
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

COMPETITIONS = [
    {"id": "164205", "name": "Rugby World Cup",              "slug": "world-cup",           "start": 1987},
    {"id": "180659", "name": "Six Nations",                  "slug": "six-nations",          "start": 1978},
    {"id": "244293", "name": "The Rugby Championship",       "slug": "rugby-championship",   "start": 1996},
    {"id": "242041", "name": "Super Rugby Pacific",          "slug": "super-rugby-pacific",  "start": 1996},
    {"id": "267979", "name": "Gallagher Premiership",        "slug": "premiership",          "start": 1998},
    {"id": "270557", "name": "United Rugby Championship",    "slug": "urc",                  "start": 2008},
    {"id": "271937", "name": "European Rugby Champions Cup", "slug": "champions-cup",        "start": 2008},
]

# Load existing player data
players_index = {}
if PLAYERS_INDEX.exists():
    for p in json.loads(PLAYERS_INDEX.read_text()):
        players_index[p["id"]] = p

athlete_cache = {}  # id -> {name, position, dob, height, weight}

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

def fetch_athlete(athlete_id):
    aid = str(athlete_id)
    if aid in athlete_cache:
        return athlete_cache[aid]
    data = get(f"{BASE}/athletes/{aid}?lang=en&region=us")
    if not data:
        return {}
    pos = data.get("position", {})
    info = {
        "id":       aid,
        "name":     data.get("fullName", ""),
        "position": pos.get("displayName", "") if isinstance(pos, dict) else "",
        "dob":      data.get("dateOfBirth", "")[:10] if data.get("dateOfBirth") else "",
        "height":   data.get("displayHeight", ""),
        "weight":   data.get("displayWeight", ""),
        "slug":     data.get("slug", ""),
    }
    athlete_cache[aid] = info
    time.sleep(0.1)
    return info

def fetch_player_stats(league_id, event_id, comp_id, team_id, player_id):
    """Fetch stats for one player in one match."""
    url = f"{BASE}/leagues/{league_id}/events/{event_id}/competitions/{comp_id}/competitors/{team_id}/roster/{player_id}/statistics/0?lang=en&region=us"
    data = get(url)
    if not data:
        return {}
    cats = data.get("splits", {}).get("categories", [])
    stats = {}
    for cat in cats:
        for s in cat.get("stats", []):
            stats[s["name"]] = s.get("value", 0)
    return stats

def fetch_match_with_players(league_id, event_id):
    """Fetch match result + all player stats."""
    # Get match summary (scores, teams, status)
    summary = get(f"{SITE}/{league_id}/summary?event={event_id}")
    if not summary:
        return None, []

    header = summary.get("header", {})
    comps  = header.get("competitions", [])
    if not comps:
        return None, []

    comp        = comps[0]
    comp_id     = comp.get("id", event_id)
    status      = comp.get("status", {})
    completed   = status.get("type", {}).get("completed", False)
    if not completed:
        return None, []

    competitors = comp.get("competitors", [])
    if len(competitors) < 2:
        return None, []

    home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

    home_team  = (home.get("team") or {}).get("displayName", "")
    away_team  = (away.get("team") or {}).get("displayName", "")
    home_id    = str(home.get("id", ""))
    away_id    = str(away.get("id", ""))
    home_score = home.get("score", "")
    away_score = away.get("score", "")
    home_winner= home.get("winner", False)
    date       = comp.get("date", "")[:10]

    game_info = summary.get("gameInfo", {})
    venue     = (game_info.get("venue") or {}).get("fullName", "")

    match = {
        "id":         str(event_id),
        "date":       date,
        "home_team":  home_team,
        "away_team":  away_team,
        "home_id":    home_id,
        "away_id":    away_id,
        "home_score": home_score,
        "away_score": away_score,
        "winner":     home_team if home_winner else away_team,
        "venue":      venue,
    }

    # Fetch player stats for both teams
    player_game_logs = []  # list of {player_id, player_info, game_stats}

    for team_id, team_name in [(home_id, home_team), (away_id, away_team)]:
        roster_url = f"{BASE}/leagues/{league_id}/events/{event_id}/competitions/{comp_id}/competitors/{team_id}/roster?lang=en&region=us"
        roster_data = get(roster_url)
        if not roster_data:
            continue

        entries = roster_data.get("entries", [])
        for entry in entries:
            pid = str(entry.get("playerId", ""))
            if not pid:
                continue

            athlete = fetch_athlete(pid)
            stats   = fetch_player_stats(league_id, event_id, comp_id, team_id, pid)

            game_log = {
                "event_id":    str(event_id),
                "date":        date,
                "competition": league_id,
                "team":        team_name,
                "opponent":    away_team if team_id == home_id else home_team,
                "home_away":   "home" if team_id == home_id else "away",
                "starter":     entry.get("starter", False),
                "jersey":      entry.get("jersey", ""),
                # Key stats
                "tries":             int(stats.get("tries", 0) or 0),
                "points":            int(stats.get("points", 0) or 0),
                "tackles":           int(stats.get("tackles", 0) or 0),
                "missed_tackles":    int(stats.get("missedTackles", 0) or 0),
                "metres":            int(stats.get("metres", 0) or 0),
                "runs":              int(stats.get("runs", 0) or 0),
                "clean_breaks":      int(stats.get("cleanBreaks", 0) or 0),
                "defenders_beaten":  int(stats.get("defendersBeaten", 0) or 0),
                "passes":            int(stats.get("passes", 0) or 0),
                "kicks":             int(stats.get("kicks", 0) or 0),
                "kick_metres":       int(stats.get("kickFromHandMetres", 0) or 0),
                "penalties":         int(stats.get("penaltiesConceded", 0) or 0),
                "yellow_cards":      int(stats.get("yellowCards", 0) or 0),
                "red_cards":         int(stats.get("redCards", 0) or 0),
                "minutes":           int(stats.get("minutesPlayedTotal", 0) or 0),
                "try_assists":       int(stats.get("tryAssists", 0) or 0),
                "offloads":          int(stats.get("offload", 0) or 0),
                "turnovers_conceded":int(stats.get("turnoversConceded", 0) or 0),
                "penalty_goals":     int(stats.get("penaltyGoals", 0) or 0),
                "conversions":       int(stats.get("conversionGoals", 0) or 0),
                "drop_goals":        int(stats.get("dropGoalsConverted", 0) or 0),
            }
            player_game_logs.append((pid, athlete, game_log))
            time.sleep(0.1)

    return match, player_game_logs

def fetch_season_event_ids(league_id, year):
    data = get(f"{BASE}/leagues/{league_id}/seasons/{year}/events?limit=200&lang=en&region=us")
    if not data:
        return []
    items = data.get("items", [])
    ids = []
    for item in items:
        ref = item.get("$ref", "")
        eid = ref.split("/events/")[-1].split("?")[0] if "/events/" in ref else item.get("id","")
        if eid:
            ids.append(str(eid))
    return ids

# ── Main loop ────────────────────────────────────────────────────────────────

DATA_DIR.joinpath("index.json").write_text(json.dumps(COMPETITIONS, separators=(",",":")))

for comp in COMPETITIONS:
    league_id   = comp["id"]
    league_name = comp["name"]
    league_dir  = DATA_DIR / league_id
    league_dir.mkdir(exist_ok=True)

    comp_start = comp.get("start", START_YEAR)
    year_start = min(START_YEAR, comp_start)

    print(f"\n{'='*50}")
    print(f"{league_name} ({league_id}) from {year_start}")

    season_index = []

    for year in range(year_start, END_YEAR + 1):
        out_file = league_dir / f"{year}.json"

        existing = []
        existing_ids = set()
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text())
                existing_ids = set(m["id"] for m in existing)
            except:
                pass

        event_ids = fetch_season_event_ids(league_id, year)
        if not event_ids:
            continue

        new_ids = [eid for eid in event_ids if eid not in existing_ids]
        if not new_ids:
            print(f"  {year}: all {len(existing)} matches already saved")
            if existing:
                season_index.append({"year": year, "matches": len(existing)})
            continue

        print(f"  {year}: {len(new_ids)} new matches to fetch")

        new_matches = []
        for i, eid in enumerate(new_ids):
            print(f"    [{i+1}/{len(new_ids)}] {eid}")
            match, player_logs = fetch_match_with_players(league_id, eid)

            if match:
                new_matches.append(match)

                # Save player game logs
                for pid, athlete, game_log in player_logs:
                    # Update player index
                    if pid not in players_index:
                        players_index[pid] = {
                            "id":       pid,
                            "name":     athlete.get("name", pid),
                            "position": athlete.get("position", ""),
                            "dob":      athlete.get("dob", ""),
                            "height":   athlete.get("height", ""),
                            "weight":   athlete.get("weight", ""),
                            "slug":     athlete.get("slug", ""),
                            "competitions": [],
                        }
                    if league_id not in players_index[pid]["competitions"]:
                        players_index[pid]["competitions"].append(league_id)

                    # Append to player file
                    pfile = PLAYERS_DIR / f"{pid}.json"
                    plog  = []
                    if pfile.exists():
                        try: plog = json.loads(pfile.read_text())
                        except: pass
                    existing_event_ids = set(g["event_id"] for g in plog)
                    if str(eid) not in existing_event_ids:
                        plog.append(game_log)
                        pfile.write_text(json.dumps(plog, separators=(",",":")))

            time.sleep(0.3)

        all_matches = sorted(existing + new_matches, key=lambda m: m.get("date",""))
        if all_matches:
            out_file.write_text(json.dumps(all_matches, indent=2))
            season_index.append({"year": year, "matches": len(all_matches)})
            print(f"  {year}: saved {len(all_matches)} matches")

        # Save player index after each season
        index_list = sorted(players_index.values(), key=lambda p: p.get("name",""))
        PLAYERS_INDEX.write_text(json.dumps(index_list, separators=(",",":")))

    league_dir.joinpath("index.json").write_text(json.dumps(season_index, separators=(",",":")))

# Final player index save
index_list = sorted(players_index.values(), key=lambda p: p.get("name",""))
PLAYERS_INDEX.write_text(json.dumps(index_list, separators=(",",":")))
print(f"\nDONE — {len(index_list)} players")
