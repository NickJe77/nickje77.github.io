import json
import time
import datetime as dt
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import pandas as pd
from bs4 import BeautifulSoup, Comment

BASE = "https://www.pro-football-reference.com"
START_YEAR = 1970
END_YEAR = dt.date.today().year

OUT_DIR = Path("docs/data/nfl")
GAMES_DIR = OUT_DIR / "games"

OUT_DIR.mkdir(parents=True, exist_ok=True)
GAMES_DIR.mkdir(parents=True, exist_ok=True)

# 🔥 REAL BROWSER HEADERS (IMPORTANT)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

session = requests.Session()
session.headers.update(HEADERS)


# -----------------------------
# SAFE REQUEST (RETRY + DELAY)
# -----------------------------
def fetch(url):
    for i in range(5):
        try:
            res = session.get(url, timeout=30)

            # Cloudflare block detection
            if "Just a moment" in res.text:
                print("Blocked by Cloudflare... retrying")
                time.sleep(5 + i * 2)
                continue

            return res.text
        except:
            time.sleep(3)

    return None


# -----------------------------
# GET SCHEDULE
# -----------------------------
def get_schedule(year):
    url = f"{BASE}/years/{year}/games.htm"
    print(f"Fetching {year}...")

    html = fetch(url)

    if not html:
        print(f"FAILED {year}")
        return []

    soup = BeautifulSoup(html, "html.parser")

    table_html = None

    # find in comments
    for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if 'id="games"' in c:
            table_html = c
            break

    # fallback
    if not table_html:
        table = soup.find("table", {"id": "games"})
        if table:
            table_html = str(table)

    if not table_html:
        print(f"NO TABLE {year}")
        return []

    try:
        df = pd.read_html(str(table_html))[0]
    except:
        print(f"PANDAS FAIL {year}")
        return []

    df = df[df["Week"] != "Week"]
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

    print(f"{year}: {len(games)} games")
    time.sleep(2)  # 🔥 slow down to avoid blocking

    return games


# -----------------------------
# BOXSCORE
# -----------------------------
def get_boxscore(url):
    html = fetch(url)

    if not html:
        return None

    try:
        tables = pd.read_html(html)
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

    with ThreadPoolExecutor(max_workers=4) as ex:  # 🔥 slower = safer
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
                print(f"{year}: {done}/{total}")

    return results


# -----------------------------
# SAVE
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
            continue

        save(GAMES_DIR / f"{year}.json", {
            "season": year,
            "games": games
        })

        all_years.append({
            "season": year,
            "games": len(games)
        })

    index = {
        "sport": "NFL",
        "start_season": START_YEAR,
        "end_season": END_YEAR,
        "updated_at_utc": dt.datetime.utcnow().isoformat(),
        "total_games": sum(x["games"] for x in all_years),
        "seasons": all_years
    }

    save(OUT_DIR / "index.json", index)

    print("DONE")


if __name__ == "__main__":
    main()
