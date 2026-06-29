#!/usr/bin/env python3
"""
NHL Name Patcher

Goes through existing boxscore files and replaces abbreviated names
(e.g. "Z. Benson") with full names fetched from the NHL player API.

Saves a player_names.json cache so each player is only fetched once.

Usage: python scripts/nhl_name_patcher.py
"""

import requests
import json
import time
from pathlib import Path

BASE_URL     = "https://api-web.nhle.com/v1"
BOXSCORE_DIR = Path("docs/data/nhl/boxscores")
NAMES_FILE   = Path("docs/data/nhl/player_names.json")

# Load existing name cache
names = {}
if NAMES_FILE.exists():
    names = json.loads(NAMES_FILE.read_text())
    print(f"Loaded {len(names)} cached names")

def get(url):
    for i in range(3):
        try:
            r = requests.get(url, timeout=30)
            if r.ok:
                return r.json()
            time.sleep(1)
        except Exception as e:
            print(f"  WARN: {e}")
            time.sleep(2)
    return {}

def fetch_name(pid):
    pid = str(pid)
    if pid in names:
        return names[pid]
    data = get(f"{BASE_URL}/player/{pid}/landing")
    if not data:
        return ""
    first = (data.get("firstName") or {}).get("default", "")
    last  = (data.get("lastName")  or {}).get("default", "")
    name  = (first + " " + last).strip()
    if name:
        names[pid] = name
    time.sleep(0.1)
    return name

def needs_full_name(name):
    """Detect names that need replacing: empty, numeric IDs, abbreviated, or single word"""
    if not name:
        return True
    # Numeric ID being used as name
    if name.strip().isdigit():
        return True
    parts = name.split()
    # Single word (no surname)
    if len(parts) < 2:
        return True
    # Abbreviated first name like 'Z. Benson'
    if len(parts[0]) <= 2 and parts[0].endswith('.'):
        return True
    return False

files = sorted(BOXSCORE_DIR.glob("*.json"))
print(f"Found {len(files)} boxscore files")

updated = 0
skipped = 0

for i, f in enumerate(files):
    try:
        data = json.loads(f.read_text())
    except:
        continue

    changed = False

    for side in ["home", "away"]:
        team = data.get(side, {})
        for group in ["skaters", "goalies"]:
            for player in team.get(group, []):
                pid = str(player.get("id", ""))
                if not pid:
                    continue
                if needs_full_name(player.get("name", "")):
                    full = fetch_name(pid)
                    if full and full != player.get("name"):
                        player["name"] = full
                        changed = True

    if changed:
        f.write_text(json.dumps(data, separators=(",", ":")))
        updated += 1
    else:
        skipped += 1

    # Save name cache every 500 files
    if (i + 1) % 500 == 0:
        NAMES_FILE.write_text(json.dumps(names, separators=(",", ":")))
        print(f"  [{i+1}/{len(files)}] updated={updated} skipped={skipped} names={len(names)}")

# Final save
NAMES_FILE.write_text(json.dumps(names, separators=(",", ":")))
print(f"\nDONE — {updated} files updated, {skipped} skipped, {len(names)} names cached")

# Update players.json index with full names
PLAYERS_INDEX = Path("docs/data/nhl/players.json")
if PLAYERS_INDEX.exists():
    players = json.loads(PLAYERS_INDEX.read_text())
    updated_index = 0
    for p in players:
        pid = str(p.get("id", ""))
        # Try both string and int key formats
        full = names.get(pid) or names.get(int(pid) if pid.isdigit() else pid)
        if full:
            p["name"] = full
            updated_index += 1
    PLAYERS_INDEX.write_text(json.dumps(players, separators=(",", ":")))
    print(f"Updated {updated_index} names in players.json")
else:
    print("players.json not found — skipping index update")
