import requests
import json
import os
from datetime import date
from io import BytesIO

try:
    import openpyxl
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl", "-q", "--break-system-packages"])
    import openpyxl

BASE = "docs/data/tennis/seasons"
CURRENT_YEAR = date.today().year
PREV_YEAR = CURRENT_YEAR - 1

HEADERS = {"User-Agent": "tennis-seasons-updater/1.0 (github-actions)"}

ROUND_MAP = {
    "1st round":    "R64",
    "2nd round":    "R32",
    "3rd round":    "R16",
    "4th round":    "R8",
    "quarterfinal": "QF",
    "quarterfinals":"QF",
    "semifinal":    "SF",
    "semifinals":   "SF",
    "final":        "F",
    "the final":    "F",
    "robin":        "RR",
    "round robin":  "RR",
}

def normalise_round(r):
    return ROUND_MAP.get(str(r).strip().lower(), str(r).strip())

def make_urls(year):
    return {
        "M": f"http://www.tennis-data.co.uk/{year}/{year}.xlsx",
        "F": f"http://www.tennis-data.co.uk/{year}w/{year}w.xlsx",
    }

def fetch(url, gender):
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
    print(f"    Columns: {headers}")

    def col(row, *names):
        for name in names:
            try:
                v = row[headers.index(name)]
                if v is not None and str(v).strip() != "":
                    return str(v).strip()
            except (ValueError, IndexError):
                pass
        return ""

    gender_char = "m" if gender == "M" else "f"

    matches = []
    for row in rows[1:]:
        raw_date = col(row, "Date")
        if not raw_date:
            continue

        # Date may be a datetime object
        if hasattr(raw_date, "strftime"):
            date_str = raw_date.strftime("%Y-%m-%d")
        else:
            date_str = str(raw_date).strip()[:10]

        winner     = col(row, "Winner")
        loser      = col(row, "Loser")
        tournament = col(row, "Tournament")
        surface    = col(row, "Surface", "Court")
        round_raw  = col(row, "Round")
        round_     = normalise_round(round_raw)

        # Score — tennis-data.co.uk stores it across set columns W1/L1, W2/L2 etc
        # Try "Score" first, then reconstruct from set columns
        score = col(row, "Score", "score")
        if not score:
            sets = []
            for i in range(1, 6):
                w = col(row, f"W{i}")
                l = col(row, f"L{i}")
                if w and l:
                    sets.append(f"{w}-{l}")
            score = " ".join(sets)

        if not winner or not loser:
            continue

        tournament_slug = tournament.replace(" ", "-").lower()
        winner_slug     = winner.replace(" ", "-").lower()
        loser_slug      = loser.replace(" ", "-").lower()
        round_slug      = round_.lower()
        year_str        = date_str[:4]

        match_id = f"{year_str}_{gender_char}_{date_str}_{tournament_slug}_{round_slug}_{winner_slug}_{loser_slug}"

        matches.append({
            "match_id":     match_id,
            "date":         date_str,
            "tournament":   tournament,
            "surface":      surface,
            "round":        round_,
            "player1":      winner,
            "player2":      loser,
            "winner":       winner,
            "loser":        loser,
            "score":        score,
            "gender":       gender,
            "best_of":      3,
            "draw_size":    0,
            "minutes":      0,
            "tourney_level": "",
            "tourney_id":   "",
            "w_ace":   0, "w_df":    0, "w_svpt":  0, "w_1stIn":  0,
            "w_1stWon":0, "w_2ndWon":0, "w_SvGms": 0, "w_bpSaved":0, "w_bpFaced":0,
            "l_ace":   0, "l_df":    0, "l_svpt":  0, "l_1stIn":  0,
            "l_1stWon":0, "l_2ndWon":0, "l_SvGms": 0, "l_bpSaved":0, "l_bpFaced":0,
        })

    wb.close()
    return matches


def filter_past(matches, year):
    today = date.today().isoformat()
    if str(year) != str(date.today().year):
        return matches
    return [m for m in matches if m["date"] <= today]


def save(year, matches):
    os.makedirs(BASE, exist_ok=True)
    path = f"{BASE}/{year}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"matches": matches}, f, indent=2)
    print(f"  ✅ Saved {path} ({len(matches)} matches)")


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
