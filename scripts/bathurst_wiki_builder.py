import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (FORCED CO-DRIVERS FIX)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"
INDEX_FILE = BASE / "index.json"

SEASONS_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1963
END_YEAR = min(datetime.utcnow().year, 2026)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})

WIKI_BASE = "https://en.wikipedia.org/wiki/"


# -----------------------
# HELPERS
# -----------------------
def clean(v):
    if v is None:
        return None
    v = str(v)
    v = re.sub(r"\[[^\]]*\]", "", v)
    v = v.replace("\xa0", " ")
    v = re.sub(r"\s+", " ", v).strip()
    return v if v else None


def safe_int(v):
    if v is None:
        return None
    m = re.search(r"^\D*(\d+)", str(v))
    return int(m.group(1)) if m else None


def extract_names(text):
    text = clean(text) or ""

    # remove brackets
    text = re.sub(r"\(.*?\)", "", text)

    # split separators
    text = text.replace(" and ", "/")
    text = text.replace("&", "/")
    text = text.replace(",", "/")

    parts = [clean(x) for x in re.split(r"\s*/\s*", text) if clean(x)]

    if len(parts) >= 2:
        return parts

    # fallback regex
    names = re.findall(r"[A-Z][A-Za-z'.-]+\s+[A-Z][A-Za-z'.-]+", text)

    if names:
        return names

    return []


def fetch(url):
    try:
        r = SESSION.get(url, timeout=30)
        if r.status_code != 200:
            return None
        return r.text
    except:
        return None


# -----------------------
# UNIQUECARS (1963–2002)
# -----------------------
def scrape_uniquecars(year):
    url = f"https://www.uniquecarsandparts.com/bathurst_{year}.htm"
    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    best = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        results = []

        for tr in rows:
            cols = [clean(td.get_text()) for td in tr.find_all("td")]
            cols = [x for x in cols if x]

            if len(cols) < 3:
                continue

            pos = safe_int(cols[0])
            if pos is None:
                continue

            drivers = extract_names(cols[1])

            results.append({
                "finish_pos": pos,
                "drivers": drivers,
                "constructor": cols[2]
            })

        if len(results) > len(best):
            best = results

    if not best:
        return None

    best.sort(key=lambda x: x["finish_pos"])

    return {
        "year": year,
        "results": best,
        "winner": best[0]["drivers"],
        "source": url
    }


# -----------------------
# WIKIPEDIA (FORCED ROW SCAN)
# -----------------------
def scrape_wikipedia(year):
    url = WIKI_BASE + quote(f"{year}_Bathurst_1000")

    html = fetch(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    best_results = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 8:
            continue

        header = " ".join([r.get_text(" ").lower() for r in rows[:3]])

        if "driver" not in header:
            continue

        results = []

        for tr in rows[1:]:
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue

            pos = safe_int(tds[0].get_text())
            if pos is None:
                continue

            # 🔥 KEY FIX: scan ENTIRE ROW for names
            row_text = " ".join([td.get_text(" ") for td in tds])
            names = extract_names(row_text)

            # remove junk (teams, brands etc)
            cleaned = []
            for n in names:
                if len(n.split()) == 2:  # only real names
                    cleaned.append(n)

            # force unique
            final = []
            seen = set()
            for n in cleaned:
                k = n.lower()
                if k not in seen:
                    final.append(n)
                    seen.add(k)

            # 🔥 CRITICAL: ensure at least 2 drivers
            if len(final) > 2:
                final = final[:2]

            constructor = None
            if len(tds) > 4:
                constructor = clean(tds[4].get_text())

            results.append({
                "finish_pos": pos,
                "drivers": final,
                "constructor": constructor
            })

        if len(results) > len(best_results):
            best_results = results

    if not best_results:
        return None

    best_results.sort(key=lambda x: x["finish_pos"])

    return {
        "year": year,
        "results": best_results,
        "winner": best_results[0]["drivers"],
        "source": url
    }


# -----------------------
# RUN (SAFE)
# -----------------------
index = []

for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n=== {year} ===")

    file_path = SEASONS_DIR / f"{year}.json"

    if year <= 2002:
        data = scrape_uniquecars(year)
    else:
        data = scrape_wikipedia(year)

    if not data:
        print("  FAILED — keeping existing")
        if file_path.exists():
            index.append({
                "year": year,
                "file": f"/data/bathurst/seasons/{year}.json"
            })
        continue

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    index.append({
        "year": year,
        "file": f"/data/bathurst/seasons/{year}.json"
    })

    print(f"  saved {len(data['results'])} results")

    time.sleep(0.3)

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print("\nDONE")
