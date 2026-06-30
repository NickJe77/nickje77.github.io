#!/usr/bin/env python3
"""
NHL Player Index Rebuilder

Rebuilds docs/data/nhl/players.json from scratch by reading every
file in docs/data/nhl/players/{id}.json. This fixes cases where the
index is missing players whose game-log files already exist
(e.g. from a run that built files locally but failed to commit
the index before a later run overwrote it).

Does NOT re-fetch anything from the API — pure local rebuild.

Usage: python scripts/nhl_rebuild_player_index.py
"""

import json
from pathlib import Path

PLAYERS_DIR  = Path("docs/data/nhl/players")
INDEX_FILE   = Path("docs/data/nhl/players.json")
NAMES_FILE   = Path("docs/data/nhl/player_names.json")

names = {}
if NAMES_FILE.exists():
    names = json.loads(NAMES_FILE.read_text())
    print(f"Loaded {len(names)} cached full names")

files = sorted(PLAYERS_DIR.glob("*.json"))
print(f"Found {len(files)} player files")

index = []

for f in files:
    pid = f.stem
    try:
        games = json.loads(f.read_text())
    except Exception as e:
        print(f"  WARN: could not read {f.name}: {e}")
        continue

    if not games:
        continue

    teams = []
    seasons = []
    position = ""
    name = names.get(pid, "")

    for g in games:
        t = g.get("team")
        if t and t not in teams:
            teams.append(t)
        s = g.get("season")
        if s is not None and s not in seasons:
            seasons.append(s)

    seasons.sort()

    index.append({
        "id":       pid,
        "name":     name or pid,
        "position": position,
        "teams":    teams,
        "seasons":  seasons,
    })

index.sort(key=lambda p: p["name"])

INDEX_FILE.write_text(json.dumps(index, separators=(",", ":")))
print(f"\nDONE — wrote {len(index)} players to {INDEX_FILE}")
