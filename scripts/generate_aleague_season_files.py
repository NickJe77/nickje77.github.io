#!/usr/bin/env python3
"""
generate_aleague_season_files.py

Your seasons/ folder is currently empty, so build_aleague_data.py's
rebuild_season_jsons() step has nothing to update (it only enriches
season files that already exist, it doesn't create new ones).

This script creates the missing docs/data/aleague/seasons/<season>.json
files from the match files that already exist in docs/data/aleague/matches/.
Each season file lists every match_id played that season. Once these
exist, build_aleague_data.py will automatically fill in the home/away
team names, scores and dates the next time it runs.

Run this once, before (or as part of) the normal A-League build.
"""

import json
from pathlib import Path

REPO_ROOT   = Path(__file__).parent.parent
MATCHES_DIR = REPO_ROOT / "docs" / "data" / "aleague" / "matches"
SEASONS_DIR = REPO_ROOT / "docs" / "data" / "aleague" / "seasons"

def main():
    if not MATCHES_DIR.exists():
        print(f"Matches directory not found: {MATCHES_DIR}")
        print("Run the zip-extraction step first.")
        return

    SEASONS_DIR.mkdir(parents=True, exist_ok=True)

    season_folders = sorted(p for p in MATCHES_DIR.iterdir() if p.is_dir())
    print(f"Found {len(season_folders)} season folders\n")

    total_games = 0
    for season_dir in season_folders:
        season_id = season_dir.name
        match_files = sorted(season_dir.glob("*.json"))

        games = []
        for mf in match_files:
            try:
                with open(mf, encoding="utf-8") as f:
                    match = json.load(f)
            except Exception as e:
                print(f"  Skipping {mf}: {e}")
                continue
            match_id = match.get("match_id")
            if not match_id:
                continue
            games.append({"match_id": match_id})

        out_path = SEASONS_DIR / f"{season_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"season": season_id, "games": games}, f, indent=2, ensure_ascii=False)

        print(f"  {season_id}: {len(games)} games -> {out_path.name}")
        total_games += len(games)

    print(f"\nDone. {len(season_folders)} season files created, {total_games} games total.")
    print("Now run build_aleague_data.py to fill in team names, scores and dates.")

if __name__ == "__main__":
    main()
