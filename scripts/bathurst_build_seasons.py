import json
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

print("BATHURST BUILDER (PATCHED + WINNER FIX)")

BASE = Path("docs/data/bathurst")
SEASONS_DIR = BASE / "seasons"

BASE.mkdir(parents=True, exist_ok=True)
SEASONS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 1963
END_YEAR = 2025


def clean(x):
    if x is None:
        return None
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x or None


def norm_key(x):
    x = clean(x) or ""
    return re.sub(r"[^a-z0-9]+", "", x.lower())


def split_driver_text(text):
    text = clean(text) or ""
    parts = re.split(r"/|,| and | & |\+", text)

    out = []
    seen = set()

    for part in parts:
        part = clean(part)
        if not part:
            continue

        if len(part.split()) < 2:
            continue

        key = norm_key(part)
        if key not in seen:
            seen.add(key)
            out.append(part)

    return out


def get_url(year):
    patterns = [
        f"{year}_Bathurst_1000",
        f"{year}_Bathurst_500",
        f"{year}_Hardie-Ferodo_1000",
        f"{year}_Hardie-Ferodo_500",
        f"{year}_Tooheys_1000",
        f"{year}_James_Hardie_1000",
        f"{year}_AMP_Bathurst_1000"
    ]

    for p in patterns:
        url = f"https://en.wikipedia.org/wiki/{p}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return url
        except:
            pass

    return None


def read_tables(url):
    try:
        tables = pd.read_html(url)
    except:
        return []

    return tables


def map_columns(df):
    out = {}
    for c in df.columns:
        name = str(c).lower()

        if "pos" in name or "position" in name:
            out["finish"] = c
        elif "driver" in name:
            out["drivers"] = c
        elif "team" in name or "entrant" in name:
            out["team"] = c
        elif "no" in name or "number" in name:
            out["car_no"] = c

    return out


def parse_entrants_map(df):
    by_car_no = {}
    by_team = {}
    by_driver = {}

    if df is None:
        return by_car_no, by_team, by_driver

    colmap = map_columns(df)

    drivers_col = colmap.get("drivers")
    team_col = colmap.get("team")
    car_no_col = colmap.get("car_no")

    if not drivers_col:
        return by_car_no, by_team, by_driver

    for _, row in df.iterrows():
        drivers = split_driver_text(row.get(drivers_col))

        if not drivers:
            continue

        entry = {
            "drivers": drivers[:2],
            "team": clean(row.get(team_col)) if team_col else None,
            "car_no": clean(row.get(car_no_col)) if car_no_col else None
        }

        if entry["car_no"]:
            by_car_no[norm_key(entry["car_no"])] = entry

        if entry["team"]:
            by_team[norm_key(entry["team"])] = entry

        for d in entry["drivers"]:
            by_driver[norm_key(d)] = entry

    return by_car_no, by_team, by_driver


def parse_results(df, entrants_by_car_no, entrants_by_team, entrants_by_driver):
    results = []

    if df is None:
        return results

    colmap = map_columns(df)

    finish_col = colmap.get("finish")
    drivers_col = colmap.get("drivers")
    team_col = colmap.get("team")
    car_no_col = colmap.get("car_no")

    if not finish_col or not drivers_col:
        return results

    for _, row in df.iterrows():

        finish_raw = clean(row.get(finish_col))

        # 🔥 FIX: fallback if missing
        if not finish_raw:
            for val in row:
                v = clean(val)
                if v and re.fullmatch(r"\d{1,2}", v):
                    finish_raw = v
                    break

        if not finish_raw or not re.fullmatch(r"\d{1,2}", finish_raw):
            continue

        finish = int(finish_raw)

        drivers = split_driver_text(row.get(drivers_col))
        team = clean(row.get(team_col)) if team_col else None
        car_no = clean(row.get(car_no_col)) if car_no_col else None

        # 🔥 FIX: co-driver backfill
        if len(drivers) < 2:
            entry = None

            if car_no and norm_key(car_no) in entrants_by_car_no:
                entry = entrants_by_car_no[norm_key(car_no)]
            elif team and norm_key(team) in entrants_by_team:
                entry = entrants_by_team[norm_key(team)]
            elif drivers:
                key = norm_key(drivers[0])
                if key in entrants_by_driver:
                    entry = entrants_by_driver[key]

            if entry:
                merged = []
                seen = set()

                for d in entry.get("drivers", []) + drivers:
                    k = norm_key(d)
                    if k not in seen:
                        seen.add(k)
                        merged.append(d)

                drivers = merged[:2]

        if not drivers:
            continue

        results.append({
            "finish": finish,
            "drivers": drivers,
            "car": team
        })

    results.sort(key=lambda x: x["finish"])
    return results


# 🔥 NEW: winner fallback
def extract_winner_from_html(soup):
    for table in soup.find_all("table", class_="wikitable"):
        for row in table.find_all("tr"):
            ths = row.find_all("th")
            tds = row.find_all("td")

            if not ths or not tds:
                continue

            pos = clean(ths[0].get_text())

            if pos == "1":
                drivers = split_driver_text(tds[0].get_text(" ", strip=True))
                team = clean(tds[-1].get_text(" ", strip=True))

                if drivers:
                    return {
                        "finish": 1,
                        "drivers": drivers[:2],
                        "car": team
                    }

    return None


def fetch_year(year):
    url = get_url(year)

    if not url:
        print(f"❌ No page {year}")
        return None

    print(f"Fetching {year} → {url}")

    tables = read_tables(url)

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    if not tables:
        return None

    results_df = tables[0]
    entrants_df = tables[1] if len(tables) > 1 else None

    entrants_by_car_no, entrants_by_team, entrants_by_driver = parse_entrants_map(entrants_df)
    results = parse_results(results_df, entrants_by_car_no, entrants_by_team, entrants_by_driver)

    # 🔥 FIX: ensure winner exists
    if not any(r["finish"] == 1 for r in results):
        winner = extract_winner_from_html(soup)
        if winner:
            results.append(winner)

    results.sort(key=lambda x: x["finish"])

    if not results:
        print(f"⚠️ No results {year}")
        return None

    return {
        "year": year,
        "results": results
    }


seasons = []

for year in range(START_YEAR, END_YEAR + 1):
    data = fetch_year(year)

    if not data:
        continue

    results = data["results"]

    winner_drivers = results[0]["drivers"]
    winner_car = results[0]["car"]

    with open(BASE / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with open(SEASONS_DIR / f"{year}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    seasons.append({
        "year": year,
        "winner_drivers": winner_drivers,
        "winner_car": winner_car
    })

    print(f"✅ Saved {year} ({len(results)} rows)")
    time.sleep(1)


seasons.sort(key=lambda x: x["year"])

with open(BASE / "seasons.json", "w", encoding="utf-8") as f:
    json.dump(seasons, f, indent=2, ensure_ascii=False)

with open(BASE / "index.json", "w", encoding="utf-8") as f:
    json.dump({
        "sport": "bathurst",
        "seasons": seasons
    }, f, indent=2, ensure_ascii=False)

print("🔥 DONE")
