import requests
import json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import re

print("TENNIS BUILDER (FINAL CLEAN VERSION)")

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
    match = re.search(r"(\d{1,2}) (\w{3})", text)
    if not match:
        return ""

    day = match.group(1).zfill(2)
    mon = MONTHS.get(match.group(2), "01")

    return f"{year}-{mon}-{day}"


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

        headers = [th.get_text(strip=True) for th in table.find_all("th")]

        # 🔥 ONLY tables that actually contain tournaments
        if not any("Tournament" in h for h in headers):
            continue

        rows = table.find_all("tr")

        for row in rows:
            cols = row.find_all("td")

            if len(cols) < 2:
                continue

            try:
                date_text = clean(cols[0].get_text())
                name = clean(cols[1].get_text())
                surface_text = clean(cols[2].get_text()) if len(cols) > 2 else ""
            except:
                continue

            # -------------------------
            # FILTER BAD ROWS
            # -------------------------
            if len(name) < 4:
                continue

            if "Davis Cup" in name:
                continue

            if "vs" in name.lower():
                continue

            if re.search(r"\d{2,}", name):
                continue

            # -------------------------
            # CLEAN NAME
            # -------------------------
            name = re.sub(r"\[.*?\]", "", name)
            name = re.sub(r"\s+", " ", name).strip()

            # -------------------------
            # SURFACE
            # -------------------------
            surface = ""
            if "Hard" in surface_text:
                surface = "Hard"
            elif "Clay" in surface_text:
                surface = "Clay"
            elif "Grass" in surface_text:
                surface = "Grass"

            # -------------------------
            # DATE
            # -------------------------
            date = parse_date(date_text, year)

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
# SAVE (OVERWRITE BAD YEARS ONLY)
# -------------------------
def save_year(year, data):
    path = BASE / f"{year}.json"

    if not data:
        print(f"⚠️ No data for {year}")
        return

    with open(path, "w") as f:
        json.dump(data, f)

    print(f"✅ Saved {year}")


# -------------------------
# MAIN
# -------------------------
for year in TARGET_YEARS:
    data = build_year(year)
    save_year(year, data)
