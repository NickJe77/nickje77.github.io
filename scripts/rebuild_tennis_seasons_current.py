import requests
import json
import os
from datetime import date
from io import BytesIO

try:
    import openpyxl
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl", "-q"])
    import openpyxl

# Output directory
BASE = "docs/data/tennis/seasons"

CURRENT_YEAR = date.today().year
PREV_YEAR = CURRENT_YEAR - 1

HEADERS = {"User-Agent": "tennis-seasons-updater/1.0 (github-actions)"}

# tennis-data.co.uk URL patterns (free, covers ATP + WTA, updated weekly)
# ATP:  http://www.tennis-data.co.uk/{year}/{year}.xlsx
# WTA:  http://www.tennis-data.co.uk/{year}w/{year}w.xlsx
def make_urls(year):
    return {
        "M": f"http://www.tennis-data.co.uk/{year}/{year}.xlsx",
        "F": f"http://www.tennis-data.co.uk/{year}w/{year}w.xlsx",
    }


def fetch(url, gender):
    """Download an xlsx from tennis-data.co.uk and parse into match dicts."""
    r = requests.get(url, timeout=60, headers=HEADERS)
    if r.status_code == 404:
        print(f"  ⚠️  Not found (404): {url}")
        return []
    r.raise_for_status()

    wb = openpyxl.load_workbook(BytesIO(r.content), read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]

    def col(row, name):
        try:
            return row[headers.index(name)]
        except (ValueError, IndexError):
            return ""

    matches = []
    for row in rows[1:]:
        # tennis-data uses "Date", "Winner", "Loser", "Tournament", "Surface", "Round", "Score"
        raw_date = col(row, "Date")
        if raw_date is None:
            continue

        # Date may be a datetime object or a string
        if hasattr(raw_date, "strftime"):
            date_str = raw_date.strftime("%Y-%m-%d")
        else:
            date_str = str(raw_date).strip()[:10]

        winner     = str(col(row, "Winner") or "").strip()
        loser      = str(col(row, "Loser")  or "").strip()
        tournament = str(col(row, "Tournament") or "").strip()

        if not winner or not loser:
            continue

        matches.append({
            "match_id":   f"{date_str}_{tournament}_{winner}_{loser}".replace(" ", "_").lower(),
            "date":       date_str,
            "tournament": tournament,
            "surface":    str(col(row, "Surface") or "").strip(),
            "round":      str(col(row, "Round")   or "").strip(),
            "player1":    winner,
            "player2":    loser,
            "winner":     winner,
            "loser":      loser,
            "score":      str(col(row, "Score")   or "").strip(),
            "gender":     gender,
        })

    wb.close()
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
    print(f"  ✅ Saved {path} ({len(data)} matches)")


def build_season(year):
    print(f"\n📅 Building {year}...")
    urls = make_urls(year)
    all_matches = []

    for gender, url in urls.items():
        label = "ATP" if gender == "M" else "WTA"
        print(f"  Fetching {label} {year}...")
        matches = fetch(url, gender)
        print(f"    → {len(matches)} matches")
        all_matches.extend(matches)

    if not all_matches:
        print(f"  ⚠️  No data found for {year}, skipping.")
        return

    filtered = filter_past(all_matches, year)
    removed  = len(all_matches) - len(filtered)
    if removed:
        print(f"  ({removed} future matches removed)")

    save(year, filtered)


def main():
    build_season(CURRENT_YEAR)
    build_season(PREV_YEAR)
    print("\n✅ DONE — files written to", BASE)


if __name__ == "__main__":
    main()
