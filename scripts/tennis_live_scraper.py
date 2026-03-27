import json
import re
import time
from pathlib import Path
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path("docs/data/tennis")
SEASONS_DIR = BASE_DIR / "seasons"
CACHE_DIR = BASE_DIR / "cache"
NAME_CACHE_FILE = CACHE_DIR / "player_name_cache.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

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
    "M": lambda d: (
        f"https://www.tennisexplorer.com/results/"
        f"?day={d.day:02d}&month={d.month:02d}&year={d.year}&type=atp-single"
    ),
    "F": lambda d: (
        f"https://www.tennisexplorer.com/results/"
        f"?day={d.day:02d}&month={d.month:02d}&year={d.year}&type=wta-single"
    ),
}

BAD_NAMES = {
    "", "info", "preview", "image", "stats", "draw", "live", "calendar",
    "today", "next day", "previous day"
}


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


def load_name_cache() -> dict:
    if not NAME_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(NAME_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_name_cache(cache: dict) -> None:
    NAME_CACHE_FILE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


NAME_CACHE = load_name_cache()


def clean_text(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def ascii_hyphen_score(value: str) -> str:
    return (
        clean_text(value)
        .replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
    )


def looks_like_player_name(name: str) -> bool:
    name = clean_text(name)
    if not name or name.lower() in BAD_NAMES:
        return False
    if len(name) < 3:
        return False
    if re.fullmatch(r"\d{1,2}:\d{2}", name):
        return False
    if name.lower() in {"united cup", "miami", "french open"}:
        return False
    return bool(re.search(r"[A-Za-z]", name))


def tidy_short_name(name: str) -> str:
    name = clean_text(name)
    name = re.sub(r"\s+\(\d+\)$", "", name)  # remove seeding like "(1)"
    name = re.sub(r"\s+\[.*?\]$", "", name)
    return clean_text(name)


def slug_to_name_bits(href: str) -> str:
    # fallback only; profile page fetch is preferred
    href = href.strip("/")
    last = href.split("/")[-1]
    last = re.sub(r"\?.*$", "", last)
    if not last:
        return ""
    last = last.replace("-", " ").strip()
    return " ".join(w.capitalize() for w in last.split())


def parse_full_name_from_player_html(html: str, fallback_short: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    title = clean_text(soup.title.get_text(" ", strip=True) if soup.title else "")
    # e.g. "Sachko Vitaliy" appears in title/search snippets
    if title:
        title = re.sub(r"\s*[-|].*$", "", title).strip()
        if (
            len(title.split()) >= 2
            and "tennis explorer" not in title.lower()
            and "result" not in title.lower()
        ):
            return title

    h1 = soup.find("h1")
    if h1:
        h1_text = clean_text(h1.get_text(" ", strip=True))
        if len(h1_text.split()) >= 2:
            return h1_text

    return fallback_short


def get_full_name(player_href: str, short_name: str) -> str:
    short_name = tidy_short_name(short_name)
    if not player_href:
        return short_name

    if player_href in NAME_CACHE:
        return NAME_CACHE[player_href]

    full_url = player_href
    if player_href.startswith("/"):
        full_url = f"https://www.tennisexplorer.com{player_href}"
    elif player_href.startswith("http"):
        full_url = player_href
    else:
        full_url = f"https://www.tennisexplorer.com/{player_href.lstrip('/')}"

    fallback = slug_to_name_bits(player_href) or short_name

    try:
        html = safe_get(full_url, tries=2, sleep_sec=1.5)
        full_name = parse_full_name_from_player_html(html, fallback)
    except Exception as e:
        print(f"Name lookup failed for {player_href}: {e}")
        full_name = fallback

    NAME_CACHE[player_href] = full_name
    return full_name


def parse_date_yyyymmdd(d: date) -> str:
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"


def parse_set_score(cols1, cols2) -> str:
    parts = []

    # On Tennis Explorer pages, set columns are the 4th+ logical data columns
    # after time and round. We inspect a safe slice rather than hardcoding exact indexes.
    max_len = min(len(cols1), len(cols2))
    for idx in range(3, min(max_len, 8)):  # enough to cover S,1,2,3,4,5 layouts
        a = clean_text(cols1[idx].get_text(" ", strip=True))
        b = clean_text(cols2[idx].get_text(" ", strip=True))

        if not a and not b:
            continue

        # skip set-count "S" column values like 2 / 1 or 2 / 0 only if later sets exist
        if idx == 3 and re.fullmatch(r"\d", a) and re.fullmatch(r"\d", b):
            continue

        if re.search(r"\d", a) and re.search(r"\d", b):
            parts.append(f"{ascii_hyphen_score(a)}-{ascii_hyphen_score(b)}")

    return " ".join(parts).strip()


def row_player_anchor(tr):
    for a in tr.find_all("a", href=True):
        txt = clean_text(a.get_text(" ", strip=True))
        href = a["href"]
        if not txt or txt.lower() in BAD_NAMES:
            continue
        if "player" in href or looks_like_player_name(txt):
            return a
    return None


def is_match_row_pair(r1, r2) -> bool:
    a1 = row_player_anchor(r1)
    a2 = row_player_anchor(r2)
    if not a1 or not a2:
        return False

    n1 = tidy_short_name(a1.get_text(" ", strip=True))
    n2 = tidy_short_name(a2.get_text(" ", strip=True))

    if not looks_like_player_name(n1) or not looks_like_player_name(n2):
        return False
    if n1 == n2:
        return False

    cols1 = r1.find_all("td")
    cols2 = r2.find_all("td")
    if len(cols1) < 4 or len(cols2) < 4:
        return False

    return True


def parse_tournament_header(tr) -> str:
    text = clean_text(tr.get_text(" ", strip=True))
    if not text:
        return ""

    # reject table headers / nav
    bad_fragments = [
        "previous day", "next day", "all matches", "atp (singles)",
        "wta (singles)", "start", "round", "today"
    ]
    low = text.lower()
    if any(b in low for b in bad_fragments):
        return ""

    # tournament headers on these pages are short labeled rows like "United Cup"
    if len(text) <= 80 and not re.search(r"\d{1,2}:\d{2}", text):
        return text

    return ""


def parse_round(cols) -> str:
    # usually second logical cell on the top row
    for idx in range(1, min(len(cols), 4)):
        txt = clean_text(cols[idx].get_text(" ", strip=True))
        if txt and len(txt) <= 10 and re.search(r"[A-Za-z]", txt):
            return txt
    return ""


def parse_day_page(day: date, gender: str) -> list[dict]:
    url = DAY_URLS[gender](day)
    print(f"Scraping {url}")

    html = safe_get(url)
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr")

    matches = []
    current_tournament = ""

    i = 0
    while i < len(rows):
        header = parse_tournament_header(rows[i])
        if header:
            current_tournament = header
            i += 1
            continue

        if i + 1 >= len(rows):
            break

        r1 = rows[i]
        r2 = rows[i + 1]

        if not is_match_row_pair(r1, r2):
            i += 1
            continue

        a1 = row_player_anchor(r1)
        a2 = row_player_anchor(r2)
        cols1 = r1.find_all("td")
        cols2 = r2.find_all("td")

        short1 = tidy_short_name(a1.get_text(" ", strip=True))
        short2 = tidy_short_name(a2.get_text(" ", strip=True))
        href1 = a1.get("href", "")
        href2 = a2.get("href", "")

        full1 = get_full_name(href1, short1)
        full2 = get_full_name(href2, short2)

        score = parse_set_score(cols1, cols2)
        rnd = parse_round(cols1)

        matches.append({
            "tournament": current_tournament,
            "surface": "",
            "round": rnd,
            "player1": full1,
            "player2": full2,
            "short_player1": short1,
            "short_player2": short2,
            "score": score,
            "date": parse_date_yyyymmdd(day),
            "gender": gender,
            "player1_url": href1,
            "player2_url": href2,
        })

        i += 2

    print(f"Parsed {len(matches)} matches for {day} {gender}")
    return matches


def iter_days(year: int):
    d = date(year, 1, 1)
    end = min(date(year, 12, 31), datetime.utcnow().date())
    while d <= end:
        yield d
        d += timedelta(days=1)


def dedupe_matches(matches: list[dict]) -> list[dict]:
    out = []
    seen = set()

    for m in matches:
        key = (
            m.get("date", ""),
            m.get("gender", ""),
            m.get("tournament", ""),
            m.get("player1", ""),
            m.get("player2", ""),
            m.get("score", ""),
            m.get("round", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(m)

    out.sort(key=lambda x: (x.get("date", ""), x.get("tournament", ""), x.get("player1", "")))
    return out


def save_year(year: int, matches: list[dict]) -> None:
    out = SEASONS_DIR / f"{year}.json"
    out.write_text(
        json.dumps(dedupe_matches(matches), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved {out}")


def main():
    print("RUNNING TENNIS DAILY SCRAPER")

    for year in YEARS:
        year_matches = []

        for d in iter_days(year):
            for gender in ("M", "F"):
                try:
                    day_matches = parse_day_page(d, gender)
                    year_matches.extend(day_matches)
                    time.sleep(0.8)
                except Exception as e:
                    print(f"FAILED {d} {gender}: {e}")
                    time.sleep(1.5)

            # save progressively so it can resume sensibly after interruptions
            save_year(year, year_matches)
            save_name_cache(NAME_CACHE)

        save_year(year, year_matches)
        save_name_cache(NAME_CACHE)

    print("DONE")


if __name__ == "__main__":
    main()
