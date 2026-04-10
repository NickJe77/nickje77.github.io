import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

print("BATHURST REBUILD 1963+ (ALL DRIVERS, NO PLACEHOLDERS)")

BASE_URL = "https://www.uniquecarsandparts.com/bathurst_{year}.htm"
OUT_DIR = Path("docs/data/bathurst")
OUT_DIR.mkdir(parents=True, exist_ok=True)

START_YEAR = 1963
END_YEAR = 2026

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

RESULT_TOKENS_STOP = {
    "Image", "back", "next"
}

STATUS_VALUES = {"DNF", "DNS", "DSQ", "DQ", "RET", "WD"}


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def driver_slug(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name


def parse_driver_list(raw: str):
    raw = clean_text(raw)
    if not raw:
        return []

    parts = re.split(r"\s*/\s*|\s+and\s+|,\s*", raw)
    drivers = [clean_text(p) for p in parts if clean_text(p)]

    seen = set()
    out = []
    for d in drivers:
        key = d.lower()
        if key not in seen:
            seen.add(key)
            out.append(d)

    return out


def parse_finish(value: str):
    value = clean_text(value)
    if value.isdigit():
        return int(value)
    return value


def parse_laps(value: str):
    value = clean_text(value)
    m = re.search(r"\d+", value)
    return int(m.group(0)) if m else None


def extract_text_lines(html: str):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n")
    lines = [clean_text(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    return lines


def find_results_start(lines):
    for i in range(len(lines) - 4):
        if (
            lines[i] == "PLACE"
            and "DRIVER" in lines[i + 1].upper()
            and lines[i + 2] == "VEHICLE"
            and lines[i + 3] == "CLASS"
            and lines[i + 4] == "LAPS"
        ):
            return i + 5
    return None


def looks_like_place_token(token: str):
    token = clean_text(token).upper()
    if token.isdigit():
        return True
    if token in STATUS_VALUES:
        return True
    return False


def parse_results_from_lines(lines):
    start = find_results_start(lines)
    if start is None:
        return []

    results = []
    i = start

    while i + 4 < len(lines):
        place = clean_text(lines[i])

        if place in RESULT_TOKENS_STOP:
            break

        if not looks_like_place_token(place):
            i += 1
            continue

        drivers_raw = clean_text(lines[i + 1])
        car = clean_text(lines[i + 2])
        race_class = clean_text(lines[i + 3])
        laps_raw = clean_text(lines[i + 4])

        if not drivers_raw or not car:
            i += 1
            continue

        drivers = parse_driver_list(drivers_raw)

        if not drivers:
            i += 1
            continue

        result = {
            "finish": parse_finish(place),
            "grid": None,
            "drivers": drivers,
            "car": car,
            "class": race_class or None,
            "laps": parse_laps(laps_raw),
            "time": None
        }

        results.append(result)
        i += 5

    return results


def fetch_year(year: int):
    url = BASE_URL.format(year=year)
    r = requests.get(url, headers=HEADERS, timeout=30)

    if r.status_code != 200:
        print(f"Skip {year}: HTTP {r.status_code}")
        return None

    lines = extract_text_lines(r.text)
    results = parse_results_from_lines(lines)

    if not results:
        print(f"Skip {year}: no parsed results")
        return None

    winners = []
    for row in results:
        if row["finish"] == 1:
            winners = row["drivers"]
            break
    if not winners and results:
        winners = results[0]["drivers"]

    race = {
        "year": year,
        "track": "Mount Panorama",
        "results": results,
        "winners": winners,
        "source": url
    }

    return race


all_years = []
all_drivers = {}

for year in range(START_YEAR, END_YEAR + 1):
    print(f"Scraping {year}...")
    race = fetch_year(year)

    if not race:
        continue

    out_file = OUT_DIR / f"{year}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(race, f, indent=2, ensure_ascii=False)

    all_years.append({
        "year": year,
        "winners": race["winners"]
    })

    for row in race["results"]:
        pos = row["finish"] if isinstance(row["finish"], int) else None

        for d in row["drivers"]:
            rec = all_drivers.setdefault(d, {
                "name": d,
                "slug": driver_slug(d),
                "starts": 0,
                "wins": 0,
                "podiums": 0
            })
            rec["starts"] += 1
            if pos == 1:
                rec["wins"] += 1
            if pos is not None and pos <= 3:
                rec["podiums"] += 1

    print(f"Saved {year}.json ({len(race['results'])} results)")

all_years.sort(key=lambda x: x["year"])
with open(OUT_DIR / "index.json", "w", encoding="utf-8") as f:
    json.dump(all_years, f, indent=2, ensure_ascii=False)

driver_list = sorted(all_drivers.values(), key=lambda x: (-x["wins"], -x["podiums"], x["name"]))
with open(OUT_DIR / "drivers.json", "w", encoding="utf-8") as f:
    json.dump(driver_list, f, indent=2, ensure_ascii=False)

print("DONE")
