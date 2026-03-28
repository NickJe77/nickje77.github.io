import json
import time
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup

BASE_DIR = Path("docs/data/tennis")
SEASONS_DIR = BASE_DIR / "seasons"
MATCHES_DIR = BASE_DIR / "matches"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)
MATCHES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

CURRENT_YEAR = datetime.utcnow().year
YEARS = [2025, CURRENT_YEAR]

URLS = {
    "M": lambda y: f"https://www.tennisexplorer.com/results/?type=ATP&year={y}",
    "F": lambda y: f"https://www.tennisexplorer.com/results/?type=WTA&year={y}",
}


# -------------------------
# HELPERS
# -------------------------

def get(url):
    return SESSION.get(url, timeout=30).text


def slug(text):
    return (
        text.lower()
        .replace(".", "")
        .replace(",", "")
        .replace("'", "")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "")
        .replace(" ", "-")
    )


def is_player_row(row):
    links = row.find_all("a")
    if not links:
        return False

    name = links[0].get_text(strip=True)

    return "." in name and len(name.split()) >= 2


def is_doubles(p1, p2):
    return "/" in p1 or "/" in p2


def is_junk_event(name):
    name = (name or "").lower()
    return any(x in name for x in [
        "futures", "itf", "challenger", "utr", "junior"
    ])


def is_tournament_row(row):
    text = row.get_text(" ", strip=True)

    # tournament rows:
    # - short
    # - no scores
    # - no player initials
    if not text:
        return False

    if any(c.isdigit() for c in text):
        return False

    if "." in text:
        return False

    return len(text) < 40


def parse_score(cols1, cols2):
    score = []

    for i in range(3, min(len(cols1), len(cols2))):
        a = cols1[i].get_text(strip=True)
        b = cols2[i].get_text(strip=True)

        if a.isdigit() and b.isdigit():
            score.append(f"{a}-{b}")

    return " ".join(score)


def extract_date(cols, year):
    try:
        raw = cols[0].get_text(strip=True)
        if "." in raw:
            d, m = raw.split(".")[:2]
            return f"{year}{int(m):02d}{int(d):02d}"
    except:
        pass

    return f"{year}0101"


# -------------------------
# PARSER
# -------------------------

def parse_page(url, gender, year):
    print(f"Scraping {url}")

    soup = BeautifulSoup(get(url), "html.parser")
    rows = soup.select("table tr")

    matches = []
    current_tournament = ""

    i = 0
    while i < len(rows) - 1:
        r1 = rows[i]
        r2 = rows[i + 1]

        # ✅ FIXED tournament detection
        if is_tournament_row(r1):
            text = r1.get_text(" ", strip=True)

            if not is_junk_event(text):
                current_tournament = text
            else:
                current_tournament = ""

            i += 1
            continue

        if not is_player_row(r1) or not is_player_row(r2):
            i += 1
            continue

        cols1 = r1.find_all("td")
        cols2 = r2.find_all("td")

        if not cols1 or not cols2:
            i += 1
            continue

        p1 = r1.find_all("a")[0].get_text(strip=True)
        p2 = r2.find_all("a")[0].get_text(strip=True)

        # ❌ REMOVE DOUBLES
        if is_doubles(p1, p2):
            i += 2
            continue

        date = extract_date(cols1, year)
        score = parse_score(cols1, cols2)

        match = {
            "match_id": f"{date}_{slug(p1)}_vs_{slug(p2)}",
            "tournament": current_tournament,
            "surface": "",
            "round": "",
            "player1": p1,
            "player2": p2,
            "score": score,
            "date": date,
            "gender": gender,
        }

        matches.append(match)
        i += 2

    print(f"✔ {len(matches)} matches parsed")
    return matches


# -------------------------
# DEDUPE
# -------------------------

def dedupe(matches):
    seen = set()
    out = []

    for m in matches:
        key = (m["date"], m["player1"], m["player2"], m["score"])
        if key in seen:
            continue
        seen.add(key)
        out.append(m)

    return out


# -------------------------
# SAVE (FULL REBUILD)
# -------------------------

def save_outputs(year, matches):
    matches = dedupe(matches)

    (MATCHES_DIR / f"{year}.json").write_text(json.dumps(matches, indent=2))
    (SEASONS_DIR / f"{year}.json").write_text(json.dumps(matches, indent=2))

    print(f"Rebuilt {year}: {len(matches)} matches")


# -------------------------
# MAIN
# -------------------------

def main():
    print("=== TENNIS SCRAPER (FIXED STRUCTURE) ===")

    for year in YEARS:
        all_matches = []

        for gender in ["M", "F"]:
            try:
                data = parse_page(URLS[gender](year), gender, year)
                all_matches.extend(data)
                time.sleep(2)
            except Exception as e:
                print("ERROR:", e)

        save_outputs(year, all_matches)

    print("=== DONE ===")


if __name__ == "__main__":
    main()
