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


def get_race(year):
    """procyclingstats serves a race's page at different URL suffixes
    depending on whether the race is finished: completed years live at
    .../overview, but an in-progress or upcoming race (like the current
    Tour) is served at .../start (or sometimes just the bare year URL)
    instead. Hitting the wrong one doesn't error — it just silently
    returns a page with no "Stages" table, which is what was happening
    here. Try each candidate and use whichever actually has stage data."""
    candidates = [
        f"race/tour-de-france/{year}/overview",
        f"race/tour-de-france/{year}/start",
        f"race/tour-de-france/{year}",
    ]
    for path in candidates:
        try:
            race = Race(path)
            stage_rows = race.stages()
        except Exception as e:
            print(f"  Tried {path}: failed — {type(e).__name__}: {e}")
            continue
        print(f"  Tried {path}: found {len(stage_rows)} stage(s)")
        if stage_rows:
            return race, stage_rows
    return None, []


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

    race, stage_rows = get_race(year)
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


def _safe(label, fn, stage_number):
    """Runs a single field-parsing call in isolation. A failure here means
    that one table/field wasn't available or didn't parse — it does NOT
    mean the whole stage is unfinished, so this returns None for just that
    field instead of aborting the entire stage entry."""
    try:
        return fn()
    except Exception as e:
        print(f"    Stage {stage_number}: couldn't parse '{label}' — "
              f"{type(e).__name__}: {e}")
        return None


def scrape_stage(year, stage_number, stage_url, total_distance):
    """Returns a dict matching the stages.json schema, or None only if the
    stage page itself can't be loaded at all (e.g. genuinely doesn't exist
    yet). Individual fields that fail to parse are set to None rather than
    discarding the whole stage."""
    try:
        stage = Stage(stage_url)
    except ExpectedParsingError as e:
        print(f"  Stage {stage_number} ({stage_url}): page not available — "
              f"{type(e).__name__}: {e}")
        return None
    except Exception as e:
        print(f"  Stage {stage_number} ({stage_url}): UNEXPECTED ERROR "
              f"— {type(e).__name__}: {e}")
        return None

    departure = _safe("departure", stage.departure, stage_number)
    arrival = _safe("arrival", stage.arrival, stage_number)
    results = _safe("results", lambda: stage.results("rider_name", "team_name", "rank"), stage_number) or []
    gc = _safe("gc", lambda: stage.gc("rider_name"), stage_number) or []
    points = _safe("points", lambda: stage.points("rider_name"), stage_number) or []
    kom = _safe("kom", lambda: stage.kom("rider_name"), stage_number) or []
    youth = _safe("youth", lambda: stage.youth("rider_name"), stage_number) or []

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

    race, stage_rows = get_race(args.year)
    if race is None:
        print(f"Could not find a working race page for {args.year} "
              f"(tried overview/start/bare-year URLs). Nothing to do.")
        return
    print(f"Found {len(stage_rows)} stage(s) on the schedule for {args.year}.")
    for i, row in enumerate(stage_rows, start=1):
        print(f"  {i}. {row.get('date')} — {row.get('stage_name')} "
              f"({row.get('stage_url')})")

    # stages_winners() only lists stages that have actually finished, so its
    # length is a reliable "how many stages are done" count — much sturdier
    # than treating a single Stage() parse failure as "nothing left to do",
    # which could wrongly halt the whole run on one bad page.
    winners_table = race.stages_winners("stage_name", "rider_name")
    completed_count = len(winners_table)
    print(f"stages_winners() reports {completed_count} completed stage(s).")

    added = []
    for i, row in enumerate(stage_rows[:completed_count], start=1):
        if (args.year, float(i)) in already_have:
            continue
        entry = scrape_stage(args.year, i, row["stage_url"], total_distance)
        if entry is None:
            # stages_winners() said this stage is done, but the detailed
            # stage page still failed to parse — a real bug worth knowing
            # about, not silently treated as "not finished yet". Fall back
            # to at least recording the winner from stages_winners() so we
            # don't lose the one thing we do know.
            fallback_winner = winners_table[i - 1].get("rider_name")
            print(f"  Falling back to stages_winners() winner for stage "
                  f"{i}: {fallback_winner}")
            entry = {
                "Year": args.year,
                "TotalTDFDistance": total_distance,
                "Stages": float(i),
                "Start": None,
                "End": None,
                "Winner of stage": fallback_winner,
                "Yellow Jersey": None,
                "Green jersey": None,
                "Polka-dot jersey": None,
                "White jersey": None,
                "Leader": None,
            }
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
