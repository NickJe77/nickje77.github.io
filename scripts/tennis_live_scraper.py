import requests
import json
import re
import time
from pathlib import Path
from datetime import datetime, timedelta

# -------------------------
# CONFIG
# -------------------------
BASE_URL = "https://www.tennisexplorer.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

MATCH_DIR = Path("docs/data/tennis/matches")
MATCH_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2025, 2026]

# -------------------------
def clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()

# -------------------------
def clean_player(name):
    name = clean(name)
    name = re.sub(r"\(.*?\)", "", name)  # remove seeds
    name = name.replace(".", "")
    return name.strip()

# -------------------------
def slug(text):
    text = clean(text).lower()
    text = re.sub(r"[().,']", "", text)
    text = re.sub(r"\s+", "-", text)
    return text

# -------------------------
def parse_score(row1, row2):
    cols1 = row1.find_all("td")
    cols2 = row2.find_all("td")

    score = []

    for i in range(3, min(len(cols1), len(cols2), 8)):
        a = cols1[i].get_text(strip=True)
        b = cols2[i].get_text(strip=True)

        if a.isdigit() and b.isdigit():
            score.append(f"{a}-{b}")

    return " ".join(score)

# -------------------------
def get_url(day, gender):
    return f"{BASE_URL}/results/?day={day.day:02d}&month={day.month:02d}&year={day.year}&type={'atp-single' if gender=='M' else 'wta-single'}"

# -------------------------
def scrape_day(day, gender):

    url = get_url(day, gender)
    print("Scraping:", url)

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        html = r.text
    except:
        return []

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.select("tr")

    matches = []
    tournament = ""

    i = 0
    while i < len(rows):

        text = clean(rows[i].get_text())

        # detect tournament header
        if " S " in text and " H " in text:
            tournament = clean(text.split(" S ")[0])
            i += 1
            continue

        if i + 1 >= len(rows):
            break

        r1 = rows[i]
        r2 = rows[i+1]

        a1 = r1.find("a")
        a2 = r2.find("a")

        if not a1 or not a2 or not tournament:
            i += 1
            continue

        p1 = clean_player(a1.get_text())
        p2 = clean_player(a2.get_text())

        score = parse_score(r1, r2)

        date_str = f"{day.year:04d}{day.month:02d}{day.day:02d}"

        match = {
            "match_id": f"{date_str}_{slug(p1)}_vs_{slug(p2)}",
            "tournament": tournament,
            "surface": "Hard",
            "round": "R32",
            "player1": p1,
            "player2": p2,
            "score": score,
            "date": date_str,
            "gender": gender
        }

        matches.append(match)
        i += 2

    return matches

# -------------------------
def load_existing(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            return []
    return []

# -------------------------
def save_year(year, new_matches):

    path = MATCH_DIR / f"{year}.json"

    # 🔥 FIX: SAFE LOAD
    existing = load_existing(path)

    combined = existing + new_matches

    # dedupe
    seen = set()
    clean_matches = []

    for m in combined:
        key = (
            m["date"],
            m["tournament"],
            m["player1"],
            m["player2"]
        )

        if key in seen:
            continue

        seen.add(key)
        clean_matches.append(m)

    clean_matches.sort(key=lambda x: (x["date"], x["tournament"]))

    path.write_text(json.dumps(clean_matches, indent=2))

    print(f"Saved {year}: {len(clean_matches)} matches")

# -------------------------
def main():

    print("=== TENNIS SCRAPER START ===")

    today = datetime.utcnow().date()

    for year in YEARS:

        start = datetime(year, 1, 1).date()
        end = min(datetime(year, 12, 31).date(), today)

        all_matches = []

        d = start
        while d <= end:

            for gender in ["M", "F"]:
                matches = scrape_day(d, gender)
                all_matches.extend(matches)

            d += timedelta(days=1)
            time.sleep(0.5)

        save_year(year, all_matches)

    print("=== DONE ===")

# -------------------------
if __name__ == "__main__":
    main()
