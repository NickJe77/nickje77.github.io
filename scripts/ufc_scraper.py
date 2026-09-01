#!/usr/bin/env python3
"""
UFC Data Scraper

Fetches UFC event and fight data from the ESPN API.

Output:
  docs/data/ufc/events.json              — index of all events
  docs/data/ufc/events/{id}.json         — full event with all fights
  docs/data/ufc/fighters.json            — index of all fighters
  docs/data/ufc/fighters/{id}.json       — fighter profile + fight history

Usage:
  python scripts/ufc_scraper.py              # all events
  python scripts/ufc_scraper.py 2024 2026    # specific year range
"""

import requests
import json
import time
import sys
from pathlib import Path
from datetime import date, timedelta

BASE      = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc"
SITE_BASE = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc"

EVENTS_DIR   = Path("docs/data/ufc/events")
FIGHTERS_DIR = Path("docs/data/ufc/fighters")
EVENTS_DIR.mkdir(parents=True, exist_ok=True)
FIGHTERS_DIR.mkdir(parents=True, exist_ok=True)

EVENTS_INDEX   = Path("docs/data/ufc/events.json")
FIGHTERS_INDEX = Path("docs/data/ufc/fighters.json")

START_YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 1993
END_YEAR   = int(sys.argv[2]) if len(sys.argv) > 2 else 2026

# CHANGED: events within this many days of "now" are always re-fetched
# even if a file already exists for them, instead of being skipped
# outright. The scraper used to treat "the file exists" as "this
# event is fully scraped", but that's only true once ESPN has posted
# final results - if a run happens to catch an event mid-card (or
# right before it starts, with zero fights marked completed yet), it
# would write a near-empty or empty fights list ONE TIME and then
# never look at that event again, permanently. That's exactly what
# happened to two recent events: one scraped with 2 of ~12 fights
# recorded, another scraped with 0 fights recorded despite the event
# having already happened by the time anyone looked at the site. This
# window gives events time to get their final results posted (and
# picked up on a subsequent weekly run) before the scraper trusts the
# cached file and stops re-checking them.
RECENT_WINDOW_DAYS = 21

# Load existing data
events_index   = {}
fighters_index = {}
if EVENTS_INDEX.exists():
    for e in json.loads(EVENTS_INDEX.read_text()):
        events_index[e["id"]] = e
if FIGHTERS_INDEX.exists():
    for f in json.loads(FIGHTERS_INDEX.read_text()):
        fighters_index[f["id"]] = f

fighter_cache = {}  # id -> full fighter data

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

def fetch_fighter(athlete_id):
    aid = str(athlete_id)
    if aid in fighter_cache:
        return fighter_cache[aid]
    data = get(f"{BASE}/athletes/{aid}?lang=en&region=us")
    if not data:
        return {}
    fighter = {
        "id":           aid,
        "name":         data.get("fullName", ""),
        "nickname":     data.get("nickname", ""),
        "dob":          data.get("dateOfBirth", ""),
        "nationality":  (data.get("citizenshipCountry") or {}).get("name", ""),
        "weight_class": (data.get("weightClass") or {}).get("text", ""),
        "height":       data.get("displayHeight", ""),
        "weight":       data.get("displayWeight", ""),
        "reach":        data.get("displayReach", ""),
        "stance":       (data.get("stance") or {}).get("text", ""),
        "headshot":     (data.get("headshot") or {}).get("href", ""),
        "slug":         data.get("slug", ""),
    }
    fighter_cache[aid] = fighter
    time.sleep(0.1)
    return fighter

def fetch_fight(event_id, comp_id):
    """Fetch full fight details including competitors, status, result."""
    url = f"{BASE}/events/{event_id}/competitions/{comp_id}?lang=en&region=us"
    data = get(url)
    if not data:
        return None

    # Status / result
    status_url = (data.get("status") or {}).get("$ref", "")
    status = get(status_url) if status_url else {}

    result_method = ""
    result_detail = ""
    round_num     = status.get("period", 0)
    time_str      = status.get("displayClock", "")
    completed     = (status.get("type") or {}).get("completed", False)

    result_obj = status.get("result") or {}
    if result_obj:
        result_method = result_obj.get("shortDisplayName", "") or result_obj.get("displayName", "")
        result_detail = result_obj.get("displayDescription", "")

    # Competitors
    fighters = []
    winner_id = None
    for comp in data.get("competitors", []):
        aid = str(comp.get("id", ""))
        is_winner = comp.get("winner", False)
        if is_winner:
            winner_id = aid
        fighter = fetch_fighter(aid)
        fighters.append({
            "id":     aid,
            "name":   fighter.get("name", aid),
            "winner": is_winner,
        })

    weight_class  = (data.get("type") or {}).get("text", "")
    card_segment  = (data.get("cardSegment") or {}).get("description", "")
    description   = data.get("description", "")  # e.g. "3 Rnd (5-5-5)"

    return {
        "id":            comp_id,
        "weight_class":  weight_class,
        "card_segment":  card_segment,
        "format":        description,
        "fighters":      fighters,
        "winner_id":     winner_id,
        "method":        result_method,
        "method_detail": result_detail,
        "round":         round_num,
        "time":          time_str,
        "completed":     completed,
    }

def fetch_event(event_id):
    """Fetch all fights for an event."""
    out_file = EVENTS_DIR / f"{event_id}.json"

    # Fetch competitions list
    comps_data = get(f"{BASE}/events/{event_id}/competitions?limit=50")
    if not comps_data:
        return None

    comp_items = comps_data.get("items", [])
    fights = []

    for item in comp_items:
        comp_ref = item.get("$ref", "")
        comp_id  = item.get("id") or comp_ref.split("/competitions/")[-1].split("?")[0]
        if not comp_id:
            continue
        fight = fetch_fight(event_id, comp_id)
        if fight:
            fights.append(fight)
        time.sleep(0.15)

    return fights

# ── Fetch event calendar ─────────────────────────────────────────────────────

print("Fetching event calendar from ESPN scoreboard...")
scoreboard = get(f"{SITE_BASE}/scoreboard")
calendar   = (scoreboard.get("leagues") or [{}])[0].get("calendar", [])
print(f"Found {len(calendar)} events in calendar")

# Also try fetching by year range using the events endpoint
all_event_refs = []

for year in range(START_YEAR, END_YEAR + 1):
    data = get(f"{BASE}/events?dates={year}&limit=200")
    if not data:
        continue
    items = data.get("items", [])
    print(f"  {year}: {len(items)} events")
    for item in items:
        ref = item.get("$ref", "")
        eid = ref.split("/events/")[-1].split("?")[0] if "/events/" in ref else item.get("id", "")
        if eid:
            all_event_refs.append({"id": str(eid), "year": year})
    time.sleep(0.2)

print(f"\nTotal events to process: {len(all_event_refs)}")

# ── Process each event ───────────────────────────────────────────────────────

for i, eref in enumerate(all_event_refs):
    eid  = eref["id"]
    year = eref["year"]

    out_file = EVENTS_DIR / f"{eid}.json"

    # CHANGED: see RECENT_WINDOW_DAYS above. Only skip re-fetching if
    # the file exists AND (we have no cached date for it, meaning it
    # predates this change and its actual age is unknown so it's left
    # alone, OR) the event is old enough that its results are safely
    # final. Anything within the recent window gets re-fetched every
    # run regardless of whether a file already exists, so an event
    # caught mid-card or pre-results on one run gets corrected on a
    # later one instead of staying wrong forever.
    cached_date = events_index.get(eid, {}).get("date", "")
    is_recent = False
    if cached_date:
        try:
            event_dt = date.fromisoformat(cached_date[:10])
            is_recent = event_dt >= (date.today() - timedelta(days=RECENT_WINDOW_DAYS))
        except ValueError:
            is_recent = False

    if out_file.exists() and not is_recent:
        print(f"  SKIP {eid} (already saved)")
        continue
    elif out_file.exists() and is_recent:
        print(f"  RE-FETCH {eid} (recent event, checking for updated results)")

    # Fetch event metadata
    meta = get(f"{BASE}/events/{eid}?lang=en&region=us")
    if not meta:
        print(f"  WARN: no metadata for {eid}")
        continue

    event_name = meta.get("name", "")
    event_date = meta.get("date", "")
    event_short = meta.get("shortName", event_name)
    venue = (meta.get("competitions") or [{}])[0].get("venue", {}) or {}
    venue_name = (venue.get("fullName") or venue.get("name") or "")

    print(f"  [{i+1}/{len(all_event_refs)}] {event_name} ({event_date[:10] if event_date else '?'})")

    fights = fetch_event(eid)
    if fights is None:
        continue
    fights = [f for f in fights if f.get("completed")]

    event_data = {
        "id":     eid,
        "name":   event_name,
        "short":  event_short,
        "date":   event_date[:10] if event_date else "",
        "year":   year,
        "venue":  venue_name,
        "fights": fights,
    }

    out_file.write_text(json.dumps(event_data, separators=(",", ":")))

    # Add to events index
    events_index[eid] = {
        "id":    eid,
        "name":  event_name,
        "short": event_short,
        "date":  event_date[:10] if event_date else "",
        "year":  year,
        "venue": venue_name,
        "fights": len(fights),
    }

    # Add fighters to index and per-fighter fight log
    for fight in fights:
        for fighter in fight.get("fighters", []):
            fid  = fighter["id"]
            info = fighter_cache.get(fid, {})

            if fid not in fighters_index:
                fighters_index[fid] = {
                    "id":           fid,
                    "name":         info.get("name", fighter["name"]),
                    "nickname":     info.get("nickname", ""),
                    "nationality":  info.get("nationality", ""),
                    "weight_class": info.get("weight_class", ""),
                    "height":       info.get("height", ""),
                    "weight":       info.get("weight", ""),
                    "reach":        info.get("reach", ""),
                    "stance":       info.get("stance", ""),
                    "headshot":     info.get("headshot", ""),
                    "slug":         info.get("slug", ""),
                }

            # Append fight to fighter's log
            fighter_file = FIGHTERS_DIR / f"{fid}.json"
            fighter_log  = []
            if fighter_file.exists():
                try:
                    fighter_log = json.loads(fighter_file.read_text())
                except:
                    pass

            # Avoid duplicates
            existing_ids = set(f["fight_id"] for f in fighter_log)
            if fight["id"] not in existing_ids:
                opp = next((f for f in fight["fighters"] if f["id"] != fid), {})
                fighter_log.append({
                    "fight_id":    fight["id"],
                    "event_id":    eid,
                    "event_name":  event_name,
                    "date":        event_data["date"],
                    "opponent_id": opp.get("id", ""),
                    "opponent":    opp.get("name", ""),
                    "weight_class": fight["weight_class"],
                    "result":      "W" if fighter["winner"] else ("L" if fight["completed"] else "NC"),
                    "method":      fight["method"],
                    "method_detail": fight["method_detail"],
                    "round":       fight["round"],
                    "time":        fight["time"],
                    "card_segment": fight["card_segment"],
                })
                fighter_file.write_text(json.dumps(fighter_log, separators=(",", ":")))

    time.sleep(0.3)

# ── Save indexes ─────────────────────────────────────────────────────────────

events_list  = sorted(events_index.values(),  key=lambda e: e.get("date",""), reverse=True)
fighters_list= sorted(fighters_index.values(), key=lambda f: f.get("name",""))

EVENTS_INDEX.write_text(json.dumps(events_list,   separators=(",", ":")))
FIGHTERS_INDEX.write_text(json.dumps(fighters_list, separators=(",", ":")))

print(f"\nDONE — {len(events_list)} events, {len(fighters_list)} fighters")
