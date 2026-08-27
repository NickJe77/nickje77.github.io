"""
Clean AFL season data files: remove confirmed junk rows.

ROOT CAUSE: at some point, a "Season Player Rankings" summary page got
scraped and merged into the per-game season files (afl_2015.json,
afl_2016.json, afl_2017.json only) as if each row were a real match
record. These rows carry round="" (no round could be assigned, because
they were never a real match) and are reliably marked by
date == "Season Player Rankings" -- confirmed as a 100% reliable,
unambiguous signal across all three affected files (every junk-date row
has round=="", every round=="" row has the junk date, no exceptions).

This has been worked around client-side in afl-player.html and
afl-player-compare.html (dropping a blank-round row when a same-match
labeled row exists), but that's a per-page patch -- any OTHER page that
reads these season files (team pages, leaderboards, records pages, etc)
still has the contamination. This script removes the junk at the
source so every consumer is fixed at once, whether or not it's been
individually patched.

Usage:
    python scripts/clean_afl_season_data.py [--dry-run]

Run from the repo root. Operates on docs/data/afl/afl_*.json in place
(unless --dry-run, which only reports counts).
"""

import argparse
import json
from pathlib import Path

DATA_DIR = Path("docs/data/afl")
JUNK_DATE_MARKER = "Season Player Rankings"


def clean_file(path, dry_run):
    with open(path) as f:
        data = json.load(f)

    before = len(data)
    junk = [r for r in data if r.get("date") == JUNK_DATE_MARKER]
    cleaned = [r for r in data if r.get("date") != JUNK_DATE_MARKER]
    after = len(cleaned)

    affected_players = sorted(set(r.get("player") for r in junk if r.get("player")))

    print(f"{path.name}: {before} -> {after} rows ({len(junk)} junk rows removed, "
          f"{len(affected_players)} distinct player(s) affected)")

    if not dry_run and junk:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)
        print(f"  WROTE cleaned file: {path}")
    elif dry_run and junk:
        print(f"  DRY RUN -- not written")

    return len(junk), affected_players


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Report what would change without writing files")
    args = parser.parse_args()

    if not DATA_DIR.exists():
        print(f"FATAL: {DATA_DIR} not found. Run this from the repo root.")
        return

    total_junk = 0
    all_affected_players = set()

    for path in sorted(DATA_DIR.glob("afl_*.json")):
        junk_count, affected = clean_file(path, args.dry_run)
        total_junk += junk_count
        all_affected_players.update(affected)

    print("")
    print(f"TOTAL junk rows {'found' if args.dry_run else 'removed'}: {total_junk}")
    print(f"TOTAL distinct players affected: {len(all_affected_players)}")
    if args.dry_run and total_junk:
        print("Re-run without --dry-run to actually write the cleaned files.")


if __name__ == "__main__":
    main()
