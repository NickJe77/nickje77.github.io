import json
import re
import time
from pathlib import Path
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

# =========================
# PATHS
# =========================

BASE_DIR = Path("docs/data/tennis")
SEASONS_DIR = BASE_DIR / "seasons"
MATCHES_DIR = BASE_DIR / "matches"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)
MATCHES_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# CONFIG
# =========================

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.tennisexplorer.com/",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

CURRENT_YEAR = datetime.utcnow().year
YEARS = [2025, CURRENT_YEAR] if CURRENT_YEAR >= 2025 else [2025]

DAY_URLS = {
    "M": lambda d: f"https://www.tennisexplorer.com/results/?day={d.day:02d}&month={d.month:02d}&year={d.year}&type=atp-single",
    "F": lambda d: f"https://www.tennisexplorer.com/results/?day={d.day:02d}&month={d.month:02d}&year={d.year}&type=wta-single",
}

START_DATES = {
    2025: date(2025, 1, 1),
    CURRENT_YEAR: date(CURRENT_YEAR, 1, 1),
}

# =========================
# HELPERS
# =========================

def safe_get(url: str, tries: int = 3):
    for _ in range(tries):
        try:
            r = SESSION.get(url, timeout=30)
            r.raise_for_status()
            return r.text
        except:
            time.sleep(2)
    return ""

def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def slug(text):
    text = clean_text(text).lower()
    text = re.sub(r"[().,']", "", text)
    text = re.sub(r"\s+", "-", text)
    return text

# 🔥 CLEAN PLAYER (FIXED)
def clean_player(name):
    name = clean_text(name)
    name = re.sub(r"\(.*?\)", "", name)  # remove seeds
    name = name.replace(".", "")         # remove dots
    return name.strip()

def iter_days(year):
    d = START_DATES[year]
    end = min(date(year,12,31), datetime.utcnow().date())
    while d <= end:
        yield d
        d += timedelta(days=1)

# =========================
# SCORE
# =========================

def parse_score(cols1, cols2):
    score = []
    for i in range(3, min(len(cols1), len(cols2), 8)):
        a = cols1[i].get_text(strip=True)
        b = cols2[i].get_text(strip=True)

        a = re.match(r"\d+", a)
        b = re.match(r"\d+", b)

        if a and b:
            score.append(f"{a.group()}-{b.group()}")

    return " ".join(score)

# =========================
# ROUND FIX (🔥 CORE FIX)
# =========================

def parse_round(raw, score):
    raw = clean_text(raw).lower()

    if "final" in raw:
        return "F"
    if "semi" in raw or raw == "sf":
        return "SF"
    if "quarter" in raw or raw == "qf":
        return "QF"

    # fallback using score length
    sets = score.split()
    if len(sets) >= 3:
        return "R32"

    return "R64"

# =========================
# TOURNAMENT HEADER
# =========================

def clean_header(text):
    text = clean_text(text)
    text = re.sub(r"\s+S\s+1\s+2\s+3\s+4\s+5.*$", "", text)
    return text.strip()

def is_junk(name):
    name = name.lower()
    return any(x in name for x in [
        "itf","challenger","futures","doubles","junior"
    ])

# =========================
# PARSER
# =========================

def parse_day(day, gender):
    url = DAY_URLS[gender](day)
    print("Scraping", url)

    html = safe_get(url)
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr")

    matches = []
    tournament = ""
    surface = ""

    i = 0
    while i < len(rows):

        text = clean_text(rows[i].get_text())

        if " S " in text and " H " in text:
            header = clean_header(text)

            if is_junk(header):
                tournament = ""
            else:
                tournament = header

            i += 1
            continue

        if i+1 >= len(rows):
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

        cols1 = r1.find_all("td")
        cols2 = r2.find_all("td")

        if len(cols1) < 4 or len(cols2) < 4:
            i += 1
            continue

        score = parse_score(cols1, cols2)
        raw_round = cols1[1].get_text(strip=True)
        rnd = parse_round(raw_round, score)

        date_str = f"{day.year:04d}{day.month:02d}{day.day:02d}"

        match = {
            "match_id": f"{date_str}_{slug(p1)}_vs_{slug(p2)}",
            "tournament": tournament,
            "surface": surface or "Hard",
            "round": rnd,
            "player1": p1,
            "player2": p2,
            "score": score,
            "date": date_str,
            "gender": gender,
        }

        matches.append(match)
        i += 2

    return matches

# =========================
# SAVE
# =========================

def save(year, matches):
    seen = set()
    clean = []

    for m in matches:
        key = (
            m["date"],
            m["tournament"],
            m["round"],
            m["player1"],
            m["player2"]
        )
        if key in seen:
            continue
        seen.add(key)
        clean.append(m)

    clean.sort(key=lambda x: (x["date"], x["tournament"]))

    (MATCHES_DIR / f"{year}.json").write_text(json.dumps(clean, indent=2))
    (SEASONS_DIR / f"{year}.json").write_text(json.dumps(clean, indent=2))

    print(f"Saved {year}: {len(clean)} matches")

# =========================
# MAIN
# =========================

def main():
    print("=== TENNIS SCRAPER START ===")

    for year in YEARS:
        all_matches = []

        for d in iter_days(year):
            for g in ["M","F"]:
                try:
                    all_matches += parse_day(d, g)
                    time.sleep(0.8)
                except Exception as e:
                    print("ERROR:", e)

        save(year, all_matches)

    print("=== DONE ===")

if __name__ == "__main__":
    main()
