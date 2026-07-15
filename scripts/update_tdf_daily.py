#!/usr/bin/env python3
"""
update_tdf_daily.py

Fetches any newly-completed Tour de France stages for a given year from
procyclingstats.com and appends them to stages.json, then recomputes
riders.json (per-year stage win counts) from the updated stage data.

Designed to run once a day during the Tour (e.g. via a scheduled GitHub
Action) against the same JSON files already living at:
    docs/data/cycling/stages.json
    docs/data/cycling/riders.json
    docs/data/cycling/leaderboard.json

It is idempotent: running it twice on the same day, or after the Tour has
finished, does nothing harmful — it only adds stages that (a) have actually
finished on procyclingstats.com and (b) aren't already present in stages.json
for that year+stage number.

leaderboard.json (the all-time cumulative table) is deliberately NOT
touched here. That table represents career totals and mixing in "still
racing this July" numbers mid-Tour risks getting it wrong (e.g. a rider's
final placing can still change). Update leaderboard.json as a separate,
manual step once the Tour has concluded for the year.

Usage:
    python3 update_tdf_daily.py --year 2026
    python3 update_tdf_daily.py --year 2026 --data-dir docs/data/cycling
    python3 update_tdf_daily.py --year 2026 --dry-run

Requires: pip install procyclingstats
"""
import argparse
import json
import sys
from pathlib import Path

from procyclingstats import Race, Stage
from procyclingstats.errors import ExpectedParsingError


def fmt_with_team(rider_name, team_name):
    """Matches the existing data's stage-winner format:
    'Jasper Philipsen  (Alpecin-Deceuninck)' — note the double space."""
    if not rider_name:
        return None
    if team_name:
        return f"{rider_name}  ({team_name})"
    return rider_name


def first_or_none(table, field):
    if not table:
        return None
    return table[0].get(field)


def get_total_distance(year, cache_path):
    """Total race distance barely matters day-to-day (it's the same for
    every stage row within a year), so this is computed once and cached
    rather than re-summed on every run."""
    cache = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text())
    key = str(year)
    if key in cache:
        return cache[key]

    race = Race(f"race/tour-de-france/{year}/overview")
    stage_rows = race.stages()
    total = 0.0
    for row in stage_rows:
        try:
            s = Stage(row["stage_url"])
            total += s.distance() or 0.0
        except ExpectedParsingError:
            continue
    total = round(total)
    cache[key] = total
    cache_path.write_text(json.dumps(cache, indent=2))
    return total


def load_json(path):
    if not path.exists():
        raise SystemExit(f"Expected data file not found: {path}")
    return json.loads(path.read_text())


def save_stages(path, stages):
    # stages.json is compact (no indent) in the existing repo — match it.
    path.write_text(json.dumps(stages))


def save_indented(path, data):
    path.write_text(json.dumps(data, indent=2))


def scrape_stage(year, stage_number, stage_url, total_distance):
    """Returns a dict matching the stages.json schema, or None if the
    stage hasn't actually finished yet (results table not published)."""
    try:
        stage = Stage(stage_url)
        results = stage.results("rider_name", "team_name", "rank")
        gc = stage.gc("rider_name")
        points = stage.points("rider_name")
        kom = stage.kom("rider_name")
        youth = stage.youth("rider_name")
        departure = stage.departure()
        arrival = stage.arrival()
    except ExpectedParsingError as e:
        # Could genuinely mean "stage hasn't happened yet" — but could also
        # mean the page structure didn't match what we expected for a
        # completed stage. Log which one so it's not a silent guess.
        print(f"  Stage {stage_number} ({stage_url}): no results yet, or "
              f"parse failed — {type(e).__name__}: {e}")
        return None
    except Exception as e:
        # Anything else (network error, unexpected HTML, etc) — surface it
        # loudly rather than treating it the same as "not finished yet".
        print(f"  Stage {stage_number} ({stage_url}): UNEXPECTED ERROR "
              f"— {type(e).__name__}: {e}")
        return None

    winner_row = next((r for r in results if r.get("rank") == 1), None)
    winner = None
    if winner_row:
        winner = fmt_with_team(winner_row.get("rider_name"), winner_row.get("team_name"))

    return {
        "Year": year,
        "TotalTDFDistance": total_distance,
        "Stages": float(stage_number),
        "Start": departure,
        "End": arrival,
        "Winner of stage": winner,
        "Yellow Jersey": first_or_none(gc, "rider_name"),
        "Green jersey": first_or_none(points, "rider_name"),
        "Polka-dot jersey": first_or_none(kom, "rider_name"),
        "White jersey": first_or_none(youth, "rider_name"),
        "Leader": None,
    }


def recompute_riders_for_year(stages, year):
    """riders.json entries are per-year stage-win counts. Recomputed fresh
    from stages.json each run rather than incremented, so it can't drift
    out of sync (e.g. if a stage result gets corrected upstream)."""
    wins = {}
    for row in stages:
        if row["Year"] != year:
            continue
        winner = row.get("Winner of stage")
        if not winner:
            continue
        wins[winner] = wins.get(winner, 0) + 1
    entries = [
        {"Name": name, "Year": year, "Wins": count,
         "Yellow": 0, "Green": 0, "PolkaDot": 0, "White": 0}
        for name, count in sorted(wins.items(), key=lambda kv: -kv[1])
    ]
    return entries


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--data-dir", default="docs/data/cycling")
    ap.add_argument("--dry-run", action="store_true",
                     help="Print what would change without writing files")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    stages_path = data_dir / "stages.json"
    riders_path = data_dir / "riders.json"
    cache_path = data_dir / ".total_distance_cache.json"

    stages = load_json(stages_path)
    riders = load_json(riders_path)

    already_have = {
        (row["Year"], row["Stages"]) for row in stages if row["Year"] == args.year
    }

    total_distance = get_total_distance(args.year, cache_path)

    race = Race(f"race/tour-de-france/{args.year}/overview")
    stage_rows = race.stages()  # ordered list of {date, stage_name, stage_url, ...}
    print(f"Race.stages() returned {len(stage_rows)} stage(s) for {args.year}.")
    for i, row in enumerate(stage_rows, start=1):
        print(f"  {i}. {row.get('date')} — {row.get('stage_name')} "
              f"({row.get('stage_url')})")

    added = []
    for i, row in enumerate(stage_rows, start=1):
        if (args.year, float(i)) in already_have:
            continue
        entry = scrape_stage(args.year, i, row["stage_url"], total_distance)
        if entry is None:
            # Stage hasn't finished yet — stop here, remaining stages are
            # further in the future too.
            break
        stages.append(entry)
        added.append(entry)
        print(f"Added stage {i}: {entry['Start']} -> {entry['End']}, "
              f"winner: {entry['Winner of stage']}")

    if not added:
        print(f"No new completed stages found for {args.year}.")
        return

    # Recompute this year's slice of riders.json, leave other years untouched
    other_years = [r for r in riders if r["Year"] != args.year]
    this_year = recompute_riders_for_year(stages, args.year)
    riders = other_years + this_year

    if args.dry_run:
        print(f"\nDRY RUN — would write {len(added)} new stage(s) and "
              f"refresh riders.json for {args.year}. No files changed.")
        return

    save_stages(stages_path, stages)
    save_indented(riders_path, riders)
    print(f"\nWrote {len(added)} new stage(s) to {stages_path}")
    print(f"Refreshed {args.year} entries in {riders_path}")
    print("Note: leaderboard.json (all-time totals) was NOT touched — "
          "update that manually once the Tour has finished.")


if __name__ == "__main__":
    main()
