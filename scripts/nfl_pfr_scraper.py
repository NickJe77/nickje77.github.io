import json
import time
import datetime as dt
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import pandas as pd

BASE = "https://www.pro-football-reference.com"
START_YEAR = 1970
END_YEAR = dt.date.today().year

OUT_DIR = Path("docs/data/nfl")
GAMES_DIR = OUT_DIR / "games"

OUT_DIR.mkdir(parents=True, exist_ok=True)
GAMES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

session = requests.Session()
session.headers.update(HEADERS)


# -----------------------------
# GET SCHEDULE (FIXED)
# -----------------------------
def get_schedule(year):
    url = f"{BASE}/years/{year}/games.htm"
    print(f"Fetching {year} schedule...")

    try:
        res = session.get(url, timeout=30)
        html = res.text

        tables = pd.read_html(html)
    except Exception as e:
        print(f"FAILED {year}: {e}")
        return []

    if not tables:
        print(f"NO TABLES {year}")
        return []

    df = tables[0]

    # remove repeated headers
    df = df[df["Week"] != "Week"]

    # remove empty rows
    df = df.dropna(subset=["Date"])

    games = []

    for _, row in df.iterrows():
        try:
            box = row.get("Boxscore")

            if not isinstance(box, str):
                continue

            game_id = box.split("/")[-1].replace(".htm", "")

            games.append({
                "season": year,
                "week": row.get("Week"),
                "date": str(row.get("Date")),
                "winner": row.get("Winner/tie"),
                "loser": row.get("Loser/tie"),
                "winner_points": int(row.get("PtsW")) if not pd.isna(row.get("PtsW")) else None,
                "loser_points": int(row.get("PtsL")) if not pd.isna(row.get("PtsL")) else None,
                "boxscore_url": BASE + box,
                "game_id": game_id
            })

        except:
            continue

    print(f"{year}: {len(games)} games found")
    return games


# -----------------------------
# GET BOXSCORE
# -----------------------------
def get_boxscore(url):
    try:
        res = session.get(url, timeout=30)
        tables = pd.read_html(res.text)
        return [t.fillna("").to_dict(orient="records") for t in tables]
    except:
        return None


# -----------------------------
# SCRAPE YEAR
# -----------------------------
def scrape_year(year):
    schedule = get_schedule(year)
    if not schedule:
        return []

    results = []

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {
            ex.submit(get_boxscore, g["boxscore_url"]): g
            for g in schedule
        }

        done = 0
        total = len(schedule)

        for fut in as_completed(futures):
            g = futures[fut]

            try:
                box = fut.result()
            except:
                box = None

            g["boxscore"] = box
            results.append(g)

            done += 1
            if done % 25 == 0 or done == total:
                print(f"{year}: {done}/{total} boxscores")

    return results


# -----------------------------
# SAVE JSON
# -----------------------------
def save(path, data):
    path.write_text(json.dumps(data, indent=2))


# -----------------------------
# MAIN
# -----------------------------
def main():
    all_years = []

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"\n--- {year} ---")

        games = scrape_year(year)

        if not games:
            print(f"Skipping {year} (no games)")
            continue

        save(GAMES_DIR / f"{year}.json", {
            "season": year,
            "games": games
        })

        all_years.append({
            "season": year,
            "games": len(games)
        })

        print(f"Saved {year}: {len(games)} games")

    index = {
        "sport": "NFL",
        "start_season": START_YEAR,
        "end_season": END_YEAR,
        "updated_at_utc": dt.datetime.utcnow().isoformat(),
        "total_games": sum(x["games"] for x in all_years),
        "seasons": all_years
    }

    save(OUT_DIR / "index.json", index)

    print("\nDONE")


if __name__ == "__main__":
    main()
