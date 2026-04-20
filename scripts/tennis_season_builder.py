import requests
import json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import re

print("TENNIS FULL SAFE BUILDER")

BASE = Path("docs/data/tennis/seasons")
BASE.mkdir(parents=True, exist_ok=True)

START_YEAR = 1968
END_YEAR = datetime.now().year

HEADERS = {"User-Agent": "Mozilla/5.0"}


# -------------------------
# CLEAN TEXT
# -------------------------
def clean(text):
    if not text:
        return ""
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -------------------------
# SAFE WRITE
# -------------------------
def safe_write(path, data):

    if not data:
        print(f"⚠️ Skipping {path} (no data)")
        return

    if path.exists():
        try:
            with open(path) as f:
                existing = json.load(f)

            if isinstance(existing, list) and len(existing) > 0:
                print(f"✅ Keeping existing {path}")
                return
        except:
            pass

    with open(path, "w") as f:
        json.dump(data, f)

    print(f"✅ Saved {path}")


# -------------------------
# BUILD YEAR
# -------------------------
def build_year(year):

    print(f"\n--- {year} ---")

    url = f"https://en.wikipedia.org/wiki/{year}_ATP_Tour"

    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print("❌ No page")
            return []
    except Exception as e:
        print("❌ Request error:", e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    tournaments = []

    tables = soup.find_all("table", {"class": "wikitable"})

    for table in tables:

        rows = table.find_all("tr")

        for row in rows:
            cols = row.find_all("td")

            if len(cols) < 2:
                continue

            name = clean(cols[0].get_text())
            surface = clean(cols[1].get_text())

            if not name or len(name) < 3:
                continue

            tournaments.append({
                "tournament": name,
                "surface": surface
            })

    # -------------------------
    # DEDUPE
    # -------------------------
    seen = set()
    clean_list = []

    for t in tournaments:
        key = t["tournament"].lower()

        if key in seen:
            continue

        seen.add(key)
        clean_list.append(t)

    print(f"Found {len(clean_list)} tournaments")

    return clean_list


# -------------------------
# MAIN LOOP (ALL YEARS)
# -------------------------
for year in range(START_YEAR, END_YEAR + 1):

    path = BASE / f"{year}.json"

    # 🔥 SKIP GOOD DATA
    if path.exists():
        try:
            with open(path) as f:
                existing = json.load(f)

            if isinstance(existing, list) and len(existing) > 0:
                print(f"Skipping {year} (already populated)")
                continue
        except:
            pass

    data = build_year(year)

    # 🔥 NEVER WRITE EMPTY
    if not data:
        print(f"⚠️ No data for {year}, not writing file")
        continue

    safe_write(path, data)
