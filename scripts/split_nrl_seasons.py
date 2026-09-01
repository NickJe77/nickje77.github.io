#!/usr/bin/env python3
"""
Splits docs/data/nrl/all_seasons.json into per-season files.
Output: docs/data/nrl/seasons/{year}.json

CHANGED: added dedup_match_players(). Whatever process generates
all_seasons.json.zip (outside this repo) has been producing matches
where the same player appears more than once in a single match's
"players" array - identical rows, same player_id, same stats,
duplicated 2x, 3x, even 4x for some 2026 matches. That inflated
career game counts on the site (e.g. Jai Arrow showing 101 games for
South Sydney Rabbitohs instead of the real 99) because
nrl-player.html counts one "game" per player row found, with no
dedup of its own.

This can't be fixed at the true source since that generator isn't in
this repo, so this script now defends against it here: for each
match, if the same player_id appears more than once in "players",
only the first occurrence is kept. This runs every time the zip is
split, so it's safe even if the upstream duplication keeps happening.
"""
import json
import os

INPUT  = "docs/data/nrl/all_seasons.json"
OUTDIR = "docs/data/nrl/seasons"

os.makedirs(OUTDIR, exist_ok=True)


def dedup_match_players(match):
    """Keep only the first row per player_id in a match's players list.
    Falls back to (player, played_for) if player_id is missing, since
    a handful of older/legacy entries may not have one."""

    seen = set()
    deduped = []

    for p in match.get("players") or []:
        key = p.get("player_id") or (p.get("player"), p.get("played_for"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    match["players"] = deduped
    return match


print("Reading %s ..." % INPUT)
with open(INPUT, encoding="utf-8") as f:
    all_matches = json.load(f)

print("Total matches: %d" % len(all_matches))

total_dupe_rows_removed = 0

by_season = {}
for match in all_matches:
    before = len(match.get("players") or [])
    match = dedup_match_players(match)
    after = len(match["players"])
    total_dupe_rows_removed += (before - after)

    season = str(match.get("season") or match.get("year") or "unknown")
    if season not in by_season:
        by_season[season] = []
    by_season[season].append(match)

if total_dupe_rows_removed:
    print("Removed %d duplicate player rows across all matches" % total_dupe_rows_removed)

for season, matches in sorted(by_season.items()):
    path = "%s/%s.json" % (OUTDIR, season)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(matches, f)
    print("  %s: %d matches -> %s" % (season, len(matches), path))

print("\nDone. %d season files written." % len(by_season))
