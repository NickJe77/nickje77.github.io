import json
import os
import re
from collections import defaultdict

BASE_DIR = "docs/data/tennis"
FULL_DB = os.path.join(BASE_DIR, "full_match_database.json")
SEASONS_DIR = os.path.join(BASE_DIR, "seasons")

TARGET_YEARS = ["2025", "2026"]


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def clean(v):
    if not v:
        return ""
    return str(v).replace("\xa0", " ").strip()


def is_bad_tournament(name):
    n = clean(name)

    if not n:
        return True

    # scorelines
    if re.search(r"\d+[-–]\d+", n):
        return True

    # long garbage strings (like your screenshot)
    if len(n.split()) > 6 and not any(x in n.lower() for x in [
        "open","masters","cup","finals","championship","wimbledon"
    ]):
        return True

    return False


def get_field(m, keys):
    for k in keys:
        v = clean(m.get(k))
        if v:
            return v
    return ""


def detect_tour(m):
    blob = str(m).lower()
    if "wta" in blob or "women" in blob:
        return "WTA"
    if "atp" in blob or "men" in blob:
        return "ATP"
    return ""


def build_season(matches, year):

    grouped = defaultdict(list)

    for m in matches:

        date = get_field(m, ["date","match_date","start_date"])
        if not date.startswith(str(year)):
            continue

        name = get_field(m, [
            "tournament",
            "tourney_name",
            "event",
            "event_name"
        ])

        if is_bad_tournament(name):
            continue

        surface = get_field(m, ["surface","court_surface"])
        location = get_field(m, ["location","city","venue"])
        tour = detect_tour(m)

        key = (name, location, surface, tour)

        grouped[key].append(date)

    output = []

    for (name, location, surface, tour), dates in grouped.items():

        dates = [d for d in dates if d]
        if not dates:
            continue

        output.append({
            "tournament": name,
            "surface": surface,
            "location": location,
            "tour": tour,
            "start_date": min(dates),
            "end_date": max(dates),
            "date": min(dates)
        })

    output.sort(key=lambda x: (x["date"], x["tournament"]))

    return output


def main():

    matches = load_json(FULL_DB)

    if not isinstance(matches, list):
        print("❌ full_match_database.json is not a list")
        return

    for year in TARGET_YEARS:
        season = build_season(matches, year)
        out = os.path.join(SEASONS_DIR, f"{year}.json")
        save_json(out, season)
        print(f"✅ {year} → {len(season)} tournaments")

    print("✅ DONE")


if __name__ == "__main__":
    main()
