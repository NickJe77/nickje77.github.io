"""
Build a lightweight player-games index from your yearly AFL match-log
files (data/afl/afl_<year>.json — one row per player per match).

Fetching every yearly file client-side just to show a "games played"
number on the draft pages would be slow (60+ years of full match logs).
Instead, this script scans all your local yearly files ONCE and produces
a small summary file: player name -> total career games (+ per-season
breakdown), which the draft pages can fetch instantly.

Usage:
    python3 build_player_games_index.py <folder-with-afl_*.json-files> <output.json>

Example (run from your site's repo root):
    python3 build_player_games_index.py docs/data/afl docs/data/afl/player_games_index.json

This will pick up every file matching afl_<year>.json in that folder
(e.g. afl_1965.json, afl_1966.json, ... afl_2026.json) and skip anything
that doesn't match that pattern (so afl_draft.json, all_australian_
results.json, or the index file itself won't be scanned as if they were
match logs).
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict


YEAR_FILE_RE = re.compile(r"afl_(\d{4})\.json$")


def find_year_files(folder: str) -> list[tuple[int, str]]:
    files = []
    for path in glob.glob(os.path.join(folder, "afl_*.json")):
        m = YEAR_FILE_RE.search(os.path.basename(path))
        if m:
            files.append((int(m.group(1)), path))
    return sorted(files)


def build_index(folder: str) -> dict:
    year_files = find_year_files(folder)
    if not year_files:
        print(f"No files matching afl_<year>.json found in {folder}", file=sys.stderr)
        return {}

    # player_name -> { "total_games": int, "seasons": {year: games_that_season}, "clubs": {club: games} }
    index = defaultdict(lambda: {"total_games": 0, "seasons": {}, "clubs": defaultdict(int)})

    for year, path in year_files:
        try:
            with open(path, encoding="utf-8") as f:
                rows = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [!] Skipping {path}: {e}", file=sys.stderr)
            continue

        season_counts = defaultdict(int)
        for row in rows:
            name = row.get("player")
            club = row.get("played_for")
            if not name:
                continue
            season_counts[(name, club)] += 1

        for (name, club), count in season_counts.items():
            entry = index[name]
            entry["total_games"] += count
            entry["seasons"][year] = entry["seasons"].get(year, 0) + count
            if club:
                entry["clubs"][club] += count

        print(f"[{year}] {path}: {len(rows)} rows processed")

    # Convert defaultdicts to plain dicts for clean JSON output
    out = {}
    for name, entry in index.items():
        out[name] = {
            "total_games": entry["total_games"],
            "seasons": entry["seasons"],
            "clubs": dict(entry["clubs"]),
        }
    return out


def main():
    ap = argparse.ArgumentParser(description="Build a player-games index from yearly AFL match logs.")
    ap.add_argument("folder", help="Folder containing afl_<year>.json files")
    ap.add_argument("out", help="Output path for the index JSON")
    args = ap.parse_args()

    index = build_index(args.folder)
    if not index:
        print("No data indexed — nothing written.", file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\nIndexed {len(index)} unique player names.")
    print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()
