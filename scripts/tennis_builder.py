import requests
import json
from pathlib import Path
from datetime import datetime

print("SAFE TENNIS FULL REBUILD")

BASE = Path("docs/data/tennis/seasons")
BASE.mkdir(parents=True, exist_ok=True)

START_YEAR = 1968
END_YEAR = datetime.now().year

HEADERS = {"User-Agent": "Mozilla/5.0"}


def safe_save(path, data):
    # ❌ never write empty data
    if not data:
        print(f"⚠️ Skipping {path} (no data)")
        return

    # ✔ if file exists and has data → KEEP IT
    if path.exists():
        try:
            with open(path) as f:
                existing = json.load(f)
            if isinstance(existing, list) and len(existing) > 0:
                print(f"✅ Keeping existing {path}")
                return
        except:
            pass

    # ✔ write only if safe
    with open(path, "w") as f:
        json.dump(data, f)

    print(f"✅ Created {path}")


def build_year(year):
    print(f"\n--- {year} ---")

    # 🔥 USE WIKIPEDIA (stable for tournaments list)
    url = f"https://en.wikipedia.org/wiki/{year}_ATP_Tour"

    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print("❌ No page")
            return []

    except Exception as e:
        print("❌ Request failed:", e)
        return []

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "html.parser")

    tournaments = []

    tables = soup.find_all("table", {"class": "wikitable"})

    for table in tables:
        rows = table.find_all("tr")

        for row in rows:
            cols = row.find_all("td")

            if len(cols) < 2:
                continue

            name = cols[0].get_text(strip=True)
            surface = cols[1].get_text(strip=True) if len(cols) > 1 else ""

            if not name or len(name) < 3:
                continue

            tournaments.append({
                "tournament": name,
                "surface": surface
            })

    # remove duplicates
    seen = set()
    clean = []

    for t in tournaments:
        key = t["tournament"].lower()

        if key in seen:
            continue

        seen.add(key)
        clean.append(t)

    print(f"Found {len(clean)} tournaments")

    return clean


# 🔥 MAIN LOOP (ALL YEARS)
for year in range(START_YEAR, END_YEAR + 1):
    path = BASE / f"{year}.json"

    # ✔ skip if already exists and has data
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
    safe_save(path, data)
