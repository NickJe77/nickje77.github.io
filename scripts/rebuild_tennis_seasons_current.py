import json
import os
from collections import defaultdict

BASE = "docs/data/tennis"
FULL_DB = os.path.join(BASE, "full_match_database.json")
OUT_DIR = os.path.join(BASE, "seasons")

YEARS = ["2025", "2026"]


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get(m, keys):
    for k in keys:
        v = m.get(k)
        if v:
            return str(v).strip()
    return ""


def detect_tour(m):
    blob = str(m).lower()
    if "wta" in blob or "women" in blob:
        return "WTA"
    if "atp" in blob or "men" in blob:
        return "ATP"
    return ""


def extract_year(m):
    d = get(m, ["date","match_date","start_date"])
    if len(d) >= 4:
        return d[:4]
    return get(m, ["season","year"])


def build(matches, year):

    grouped = defaultdict(list)

    for m in matches:

        if extract_year(m) != year:
            continue

        name = get(m, [
            "tournament",
            "tourney_name",
            "event",
            "event_name",
            "competition",
            "name"
        ])

        # 🔥 fallback: don't kill data
        if not name:
            name = "Unknown Event"

        surface = get(m, ["surface","court_surface"])
        location = get(m, ["location","city","venue"])
        tour = detect_tour(m)
        date = get(m, ["date","match_date","start_date"])

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

    matches = load(FULL_DB)

    for y in YEARS:
        data = build(matches, y)
        save(f"{OUT_DIR}/{y}.json", data)
        print(y, len(data))


if __name__ == "__main__":
    main()
