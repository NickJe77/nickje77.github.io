import requests
import json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import re

print("TENNIS BUILDER (CLEAN + DATED)")

BASE = Path("docs/data/tennis/seasons")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

TARGET_YEARS = [2025, 2026]

MONTHS = {
    "Jan":"01","Feb":"02","Mar":"03","Apr":"04","May":"05","Jun":"06",
    "Jul":"07","Aug":"08","Sep":"09","Oct":"10","Nov":"11","Dec":"12"
}


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
# PARSE DATE
# -------------------------
def parse_date(text, year):

    # match things like "10 Aug" or "10 Aug 17 Aug"
    match = re.search(r"(\d{1,2}) (\w{3})", text)

    if not match:
        return ""

    day = match.group(1).zfill(2)
    mon = MONTHS.get(match.group(2), "01")

    return f"{year}-{mon}-{day}"


# -------------------------
# EXTRACT NAME + SURFACE
# -------------------------
def extract_name_surface(text):

    # remove prize money, draws etc
    text = re.split(r"ATP|WTA|\$|€", text)[0]

    # remove location duplication
    text = re.sub(r"([A-Za-z])\1{2,}", r"\1", text)

    text = text.strip()

    # surface
    surface = ""
    if "Hard" in text:
        surface = "Hard"
    elif "Clay" in text:
        surface = "Clay"
    elif "Grass" in text:
        surface = "Grass"

    # remove trailing surface words from name
    name = re.sub(r"(Hard|Clay|Grass).*", "", text).strip()

    return name, surface


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

            if len(cols) < 1:
                continue

            raw_text = clean(row.get_text())

            if len(raw_text) < 5:
                continue

            date = parse_date(raw_text, year)
            name, surface = extract_name_surface(raw_text)

            if not name:
                continue

            tournaments.append({
                "tournament": name,
                "surface": surface,
                "date": date
            })

    # -------------------------
    # DEDUPE
    # -------------------------
    seen = set()
    clean_list = []

    for t in tournaments:
        key = (t["tournament"].lower(), t["date"])

        if key in seen:
            continue

        seen.add(key)
        clean_list.append(t)

    print(f"Found {len(clean_list)} tournaments")

    return clean_list


# -------------------------
# SAFE WRITE
# -------------------------
def safe_write(path, data):

    if not data:
        print(f"⚠️ No data, skipping {path}")
        return

    with open(path, "w") as f:
        json.dump(data, f)

    print(f"✅ Saved {path}")


# -------------------------
# MAIN
# -------------------------
for year in TARGET_YEARS:

    path = BASE / f"{year}.json"

    data = build_year(year)

    if not data:
        continue

    safe_write(path, data)
