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

# Tennis Explorer daily singles pages
DAY_URLS = {
    "M": lambda d: (
        f"https://www.tennisexplorer.com/results/"
        f"?day={d.day:02d}&month={d.month:02d}&year={d.year}&type=atp-single"
    ),
    "F": lambda d: (
        f"https://www.tennisexplorer.com/results/"
        f"?day={d.day:02d}&month={d.month:02d}&year={d.year}&type=wta-single"
    ),
}

# only pull from 2025 onwards, but scrape daily pages so the files actually change
START_DATES = {
    2025: date(2025, 1, 1),
    CURRENT_YEAR: date(CURRENT_YEAR, 1, 1),
}

# =========================
# HELPERS
# =========================

def safe_get(url: str, tries: int = 3, sleep_sec: float = 2.0) -> str:
    last_err = None
    for attempt in range(1, tries + 1):
        try:
            r = SESSION.get(url, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_err = e
            print(f"GET failed ({attempt}/{tries}) {url} -> {e}")
            time.sleep(sleep_sec)
    raise last_err


def clean_text(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(text: str) -> str:
    text = clean_text(text).lower()
    text = text.replace("/", "-")
    text = re.sub(r"[().,']", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def iter_days_for_year(year: int):
    start = START_DATES.get(year, date(year, 1, 1))
    end = min(date(year, 12, 31), datetime.utcnow().date())
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def extract_digits_only(text: str) -> str:
    return "".join(ch for ch in text if ch.isdigit())


def normalize_set_value(text: str) -> str:
    """
    Tennis Explorer often emits things like 6^{2}
    We only want the leading game count for the set: 6
    """
    text = clean_text(text)
    if not text:
        return ""

    # strip common superscript-ish artifacts after the main set number
    m = re.match(r"^(\d+)", text)
    if m:
        return m.group(1)

    return ""


def parse_score_from_pair(cols1, cols2) -> str:
    """
    Daily pages look like:
    Start | Round | S | 1 | 2 | 3 | 4 | 5 | H | A | info

    We skip:
    - col 0 = time
    - col 1 = round
    - col 2 = S (sets won)
    and only read actual set columns.
    """
    score_parts = []
    max_len = min(len(cols1), len(cols2))

    # set columns begin at index 3 on these pages
    for idx in range(3, min(max_len, 8)):
        a = normalize_set_value(cols1[idx].get_text(" ", strip=True))
        b = normalize_set_value(cols2[idx].get_text(" ", strip=True))

        if a and b:
            score_parts.append(f"{a}-{b}")

    return " ".join(score_parts)


def is_player_like(name: str) -> bool:
    name = clean_text(name)
    if not name:
        return False
    if len(name) < 3:
        return False
    if "/" in name:
        return False
    if re.fullmatch(r"\d{1,2}:\d{2}", name):
        return False
    return bool(re.search(r"[A-Za-z]", name))


def first_player_anchor(tr):
    for a in tr.find_all("a", href=True):
        txt = clean_text(a.get_text(" ", strip=True))
        if is_player_like(txt):
            return a
    return None


def is_match_pair(r1, r2) -> bool:
    a1 = first_player_anchor(r1)
    a2 = first_player_anchor(r2)
    if not a1 or not a2:
        return False

    n1 = clean_text(a1.get_text(" ", strip=True))
    n2 = clean_text(a2.get_text(" ", strip=True))

    if not n1 or not n2 or n1 == n2:
        return False

    cols1 = r1.find_all("td")
    cols2 = r2.find_all("td")
    if len(cols1) < 4 or len(cols2) < 4:
        return False

    return True


def parse_round_from_top_row(cols1) -> str:
    if len(cols1) < 2:
        return ""

    rnd = clean_text(cols1[1].get_text(" ", strip=True))
    return rnd


def clean_tournament_header(text: str) -> str:
    """
    Headers from results pages often look like:
    'French Open S 1 2 3 4 5 H A'
    or
    'United Cup S 1 2 3 4 5 H A'
    """
    text = clean_text(text)
    text = re.sub(r"\s+S\s+1\s+2\s+3\s+4\s+5\s+H\s+A.*$", "", text).strip()
    return text


def is_junk_event(name: str) -> bool:
    name = (name or "").lower()
    return any(x in name for x in [
        "futures",
        "itf",
        "challenger",
        "utr",
        "junior",
        "exhibition",
        "mixed",
        "doubles",
        "qual."
    ])


def parse_tournament_header_row(tr) -> str:
    text = clean_text(tr.get_text(" ", strip=True))
    if not text:
        return ""

    low = text.lower()

    # reject nav / date / control rows
    bad_fragments = [
        "previous day",
        "next day",
        "all matches",
        "atp (singles)",
        "atp (doubles)",
        "wta (singles)",
        "wta (doubles)",
        "mixed",
        "today",
        "calendar"
    ]
    if any(x in low for x in bad_fragments):
        return ""

    # must look like a tournament header line with score columns
    if " s " not in f" {low} " or " h " not in f" {low} " or " a" not in low:
        return ""

    cleaned = clean_tournament_header(text)
    if not cleaned:
        return ""

    if is_junk_event(cleaned):
        return "__JUNK__"

    return cleaned


def parse_surface_from_tournament_name(name: str) -> str:
    """
    Tennis Explorer daily results headers usually do not carry surface directly.
    Leave blank unless clearly embedded.
    """
    low = (name or "").lower()
    if "clay" in low:
        return "Clay"
    if "grass" in low:
        return "Grass"
    if "hard" in low:
        return "Hard"
    if "indoor" in low or "indoors" in low:
        return "Indoor"
    return ""


def dedupe(matches: list[dict]) -> list[dict]:
    seen = set()
    out = []

    for m in matches:
        key = (
            m.get("date", ""),
            m.get("gender", ""),
            m.get("tournament", ""),
            m.get("round", ""),
            m.get("player1", ""),
            m.get("player2", ""),
            m.get("score", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(m)

    out.sort(key=lambda x: (x.get("date", ""), x.get("tournament", ""), x.get("player1", "")))
    return out


def save_outputs(year: int, matches: list[dict]) -> None:
    clean = dedupe(matches)

    matches_file = MATCHES_DIR / f"{year}.json"
    seasons_file = SEASONS_DIR / f"{year}.json"

    matches_file.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")
    seasons_file.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Saved {year}: {len(clean)} matches")


# =========================
# PARSER
# =========================

def parse_day_page(day: date, gender: str) -> list[dict]:
    url = DAY_URLS[gender](day)
    print(f"Scraping {url}")

    html = safe_get(url)
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr")

    matches = []
    current_tournament = ""
    current_surface = ""

    i = 0
    while i < len(rows):
        # tournament header row
        header = parse_tournament_header_row(rows[i])
        if header:
            if header == "__JUNK__":
                current_tournament = ""
                current_surface = ""
            else:
                current_tournament = header
                current_surface = parse_surface_from_tournament_name(header)
            i += 1
            continue

        if i + 1 >= len(rows):
            break

        r1 = rows[i]
        r2 = rows[i + 1]

        if not current_tournament:
            i += 1
            continue

        if not is_match_pair(r1, r2):
            i += 1
            continue

        a1 = first_player_anchor(r1)
        a2 = first_player_anchor(r2)

        p1 = clean_text(a1.get_text(" ", strip=True))
        p2 = clean_text(a2.get_text(" ", strip=True))

        # singles only
        if "/" in p1 or "/" in p2:
            i += 2
            continue

        cols1 = r1.find_all("td")
        cols2 = r2.find_all("td")

        score = parse_score_from_pair(cols1, cols2)
        rnd = parse_round_from_top_row(cols1)

        date_str = f"{day.year:04d}{day.month:02d}{day.day:02d}"

        match = {
            "match_id": f"{date_str}_{slug(p1)}_vs_{slug(p2)}",
            "tournament": current_tournament,
            "surface": current_surface,
            "round": rnd,
            "player1": p1,
            "player2": p2,
            "score": score,
            "date": date_str,
            "gender": gender,
        }

        matches.append(match)
        i += 2

    print(f"Parsed {len(matches)} matches for {day} {gender}")
    return matches


# =========================
# MAIN
# =========================

def main():
    print("=== TENNIS DAILY SCRAPER START ===")

    for year in YEARS:
        year_matches = []

        for day in iter_days_for_year(year):
            for gender in ("M", "F"):
                try:
                    day_matches = parse_day_page(day, gender)
                    year_matches.extend(day_matches)
                    time.sleep(0.8)
                except Exception as e:
                    print(f"FAILED {day} {gender}: {e}")
                    time.sleep(1.5)

        save_outputs(year, year_matches)

    print("=== DONE ===")


if __name__ == "__main__":
    main()
