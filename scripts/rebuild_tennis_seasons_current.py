import json
import os
from collections import defaultdict

BASE = "docs/data/tennis"
FULL_DB = os.path.join(BASE, "full_match_database.json")
OUT = os.path.join(BASE, "seasons")

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


def extract_year(m):
    d = get(m, ["date","match_date","start_date"])
    if len(d) >= 4:
        return d[:4]
    return ""


def clean_name(name):
    # strip score junk if present
    if " 6-" in name or " 7-" in name:
        parts = name.split(" ")
        name = " ".join([p for p in parts if "-" not in p])
    return name.strip()


def build(matches, year):

    grouped = defaultdict(list)

    for m in matches:

        if extract_year(m) != year:
            continue

        # 🔥 try every possible field (this is the fix)
        name = get(m, [
            "tournament",
            "tourney_name",
            "event",
            "event_name",
            "competition",
            "name"
        ])

        if not name:
            continue

        name = clean_name(name)

        # ignore obvious player-only junk
        if len(name.split()) > 5 and "Open" not in name and "Masters" not in name:
            continue

        date = get(m, ["date","match_date","start_date"])
        if not date:
            continue

        grouped[name].append(date)

    output = []

    for name, dates in grouped.items():

        dates = sorted(dates)

        output.append({
            "tournament": name,
            "surface": "",
            "location": "",
            "tour": "",
            "start_date": dates[0],
            "end_date": dates[-1],
            "date": dates[0]
        })

    output.sort(key=lambda x: (x["date"], x["tournament"]))

    return output


def main():

    matches = load(FULL_DB)

    for y in YEARS:
        data = build(matches, y)
        save(f"{OUT}/{y}.json", data)
        print(y, len(data))


if __name__ == "__main__":
    main()
