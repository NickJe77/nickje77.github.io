#!/usr/bin/env python3
"""
Splits docs/data/nrl/all_seasons.json into per-season files.
Output: docs/data/nrl/seasons/{year}.json
"""
import json
import os

INPUT  = "docs/data/nrl/all_seasons.json"
OUTDIR = "docs/data/nrl/seasons"

os.makedirs(OUTDIR, exist_ok=True)

print("Reading %s ..." % INPUT)
with open(INPUT, encoding="utf-8") as f:
    all_matches = json.load(f)

print("Total matches: %d" % len(all_matches))

by_season = {}
for match in all_matches:
    season = str(match.get("season") or match.get("year") or "unknown")
    if season not in by_season:
        by_season[season] = []
    by_season[season].append(match)

for season, matches in sorted(by_season.items()):
    path = "%s/%s.json" % (OUTDIR, season)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(matches, f)
    print("  %s: %d matches -> %s" % (season, len(matches), path))

print("\nDone. %d season files written." % len(by_season))
