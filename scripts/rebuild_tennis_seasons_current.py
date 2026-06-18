import requests
import csv
import json
import os
from datetime import date

# Output directory
BASE = "docs/data/tennis/seasons"

CURRENT_YEAR = date.today().year
PREV_YEAR = CURRENT_YEAR - 1

def make_urls(year):
    return (
        f"https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_{year}.csv",
        f"https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master/wta_matches_{year}.csv",
    )

HEADERS = {"User-Agent": "tennis-seasons-updater/1.0 (github-actions)"}

def fetch(url, gender):
    """Fetch and parse a JeffSackmann CSV. Returns [] if the file doesn't exist yet."""
    r = requests.get(url, timeout=60, headers=HEADERS)
    if r.status_code == 404:
        print(f"  ⚠️  Not found (404): {url}")
        return []
    r.raise_for_status()

    reader = csv.DictReader(r.text.splitlines())
    matches = []
    for row in reader:
        td = row.get("tourney_date", "")
        if len(td) == 8 and td.isdigit():
            date_str = f"{td[:4]}-{td[4:6]}-{td[6:8]}"
        else:
            date_str = td

        winner     = row.get("winner_name", "")
        loser      = row.get("loser_name", "")
        tournament = row.get("tourney_name", "")

        matches.append({
            "match_id":   f"{date_str}_{tournament}_{winner}_{loser}".replace(" ", "_").lower(),
            "date":       date_str,
            "tournament": tournament,
            "surface":    row.get("surface", ""),
            "round":      row.get("round", ""),
            "player1":    winner,
            "player2":    loser,
            "winner":     winner,
            "loser":      loser,
            "score":      row.get("score", ""),
            "gender":     gender,
        })
    return matches

def filter_past(matches, year):
    """For the current year only, strip matches that haven't happened yet."""
    today = date.today().isoformat()
    if str(year) != str(date.today().year):
        return matches
    return [m for m in matches if m["date"] <= today]

def save(year, data):
    os.makedirs(BASE, exist_ok=True)
    path = f"{BASE}/{year}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  ✅ Saved {path}")

def build_season(year):
    print(f"\n📅 Building {year}...")
    atp_url, wta_url = make_urls(year)

    print(f"  Fetching ATP {year}...")
    atp = fetch(atp_url, "M")

    print(f"  Fetching WTA {year}...")
    wta = fetch(wta_url, "F")

    all_matches = atp + wta
    if not all_matches:
        print(f"  ⚠️  No data found for {year}, skipping.")
        return

    filtered = filter_past(all_matches, year)
    removed  = len(all_matches) - len(filtered)

    print(f"  {len(filtered)} matches" + (f" ({removed} future removed)" if removed else ""))
    save(year, filtered)

def main():
    # Always rebuild current year (real data, future matches filtered out)
    build_season(CURRENT_YEAR)

    # Also try previous year in case it's still being backfilled
    build_season(PREV_YEAR)

    print("\n✅ DONE — files written to", BASE)

if __name__ == "__main__":
    main()
