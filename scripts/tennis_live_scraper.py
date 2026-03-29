import requests
import json
from pathlib import Path
from datetime import datetime

print("TENNIS LIVE SCRAPER (MATCHES FIX)")

BASE_DIR = Path("docs/data/tennis")
SEASON_DIR = BASE_DIR / "seasons"
MATCH_DIR = BASE_DIR / "matches"

SEASON_DIR.mkdir(parents=True, exist_ok=True)
MATCH_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2025, 2026]

# -----------------------------
# DUMMY SCRAPER (REPLACE WITH REAL SOURCE LATER)
# -----------------------------
def get_matches(year):
    # This ensures files ALWAYS exist
    # You can replace this later with real scraping
    return []

# -----------------------------
# MAIN LOOP
# -----------------------------
for year in YEARS:
    print(f"\nProcessing {year}")

    matches = get_matches(year)

    # -----------------------------
    # SAVE MATCHES FILE (CRITICAL FIX)
    # -----------------------------
    match_output = {
        "season": year,
        "matches": matches
    }

    match_path = MATCH_DIR / f"{year}.json"
    match_path.write_text(json.dumps(match_output, indent=2))

    print(f"✅ Matches saved: {match_path}")

    # -----------------------------
    # ALSO SAVE SEASONS (IF NEEDED)
    # -----------------------------
    season_output = {
        "season": year,
        "matches": matches
    }

    season_path = SEASON_DIR / f"{year}.json"
    season_path.write_text(json.dumps(season_output, indent=2))

    print(f"✅ Season saved: {season_path}")

print("\nDONE")
