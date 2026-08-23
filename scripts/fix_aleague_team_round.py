#!/usr/bin/env python3
"""
Fix A-League match JSON files where team names have round/stage text
concatenated onto the end, e.g. "Sydney FCFinals Week 1,"
should become "Sydney FC" with round="Finals Week 1".

Run from the repo root:
    python3 scripts/fix_aleague_team_round.py data/aleague/matches

This is meant to be run by the GitHub Action
(.github/workflows/fix-aleague-team-round.yml) -- it walks every
match JSON file, fixes home_team/away_team and every team field
inside scorers/yellow_cards/red_cards, and fills in "round" if empty.
"""

import json
import sys
from pathlib import Path

KNOWN_TEAMS = [
    "Adelaide United",
    "Auckland FC",
    "Brisbane Roar",
    "Central Coast Mariners",
    "Gold Coast United",
    "Macarthur FC",
    "Melbourne City",
    "Melbourne Heart",
    "Melbourne Victory",
    "Newcastle Jets",
    "New Zealand Knights",
    "North Queensland Fury",
    "Perth Glory",
    "Queensland Roar",
    "Sydney FC",
    "Wellington Phoenix",
    "Western Sydney Wanderers",
    "Western United",
]

TEAMS_SORTED = sorted(KNOWN_TEAMS, key=len, reverse=True)


def split_team_and_round(value):
    if not isinstance(value, str):
        return value, None
    stripped = value.strip()
    for team in TEAMS_SORTED:
        if stripped == team:
            return team, None
        if stripped.startswith(team) and len(stripped) > len(team):
            remainder = stripped[len(team):].strip().strip(",").strip()
            if remainder:
                return team, remainder
    return value, None


def fix_match_json(data, unmatched_log, path_name):
    changed = False
    found_round = None

    def fix_field(obj, key):
        nonlocal changed, found_round
        if key in obj and isinstance(obj[key], str) and obj[key]:
            clean, round_text = split_team_and_round(obj[key])
            if round_text:
                obj[key] = clean
                found_round = found_round or round_text
                changed = True
            elif clean != obj[key]:
                obj[key] = clean
                changed = True
            else:
                original = obj[key]
                if not any(original.strip() == t for t in KNOWN_TEAMS):
                    unmatched_log.add((path_name, key, original))

    fix_field(data, "home_team")
    fix_field(data, "away_team")

    for section in ("scorers", "yellow_cards", "red_cards"):
        for event in data.get(section, []) or []:
            fix_field(event, "team")

    if found_round and not data.get("round"):
        data["round"] = found_round
        changed = True

    return changed


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_aleague_team_round.py <folder>")
        sys.exit(1)

    root = Path(sys.argv[1])
    if not root.exists():
        print(f"Folder not found: {root}")
        sys.exit(1)

    json_files = sorted(root.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files under {root}\n")

    fixed_count = 0
    unmatched_log = set()

    for path in json_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  SKIP (couldn't parse): {path} -- {e}")
            continue

        changed = fix_match_json(data, unmatched_log, path.name)

        if changed:
            fixed_count += 1
            print(f"  FIXED: {path.relative_to(root)}")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

    print(f"\nFixed {fixed_count} of {len(json_files)} files.")

    if unmatched_log:
        print(f"\n{len(unmatched_log)} field(s) didn't match any known team name:")
        for fname, key, value in sorted(unmatched_log):
            print(f"  {fname} [{key}]: {value!r}")


if __name__ == "__main__":
    main()
