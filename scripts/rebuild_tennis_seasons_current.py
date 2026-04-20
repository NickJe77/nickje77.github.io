import json
import os
from collections import defaultdict
from datetime import datetime

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


def parse_date(d):
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d")
    except:
        return None


def extract_year(m):
    d = get(m, ["date","match_date"])
    return d[:4] if len(d) >= 4 else ""


def build(matches, year):

    grouped = defaultdict(list)

    for m in matches:

        if extract_year(m) != year:
            continue

        date_str = get(m, ["date","match_date"])
        dt = parse_date(date_str)
        if not dt:
            continue

        # 🔥 KEY FIX: group by week (this matches tennis calendar)
        week = dt.strftime("%Y-%W")

        name = get(m, [
            "tournament",
            "tourney_name",
            "event",
            "event_name"
        ])

        if not name:
            name = f"Week {week}"

        surface = get(m, ["surface","court_surface"])
        location = get(m, ["location","city"])

        key = (week, name)

        grouped[key].append({
            "date": dt,
            "surface": surface,
            "location": location
        })

    output = []

    for (week, name), items in grouped.items():

        dates = sorted([i["date"] for i in items])

        output.append({
            "tournament": name,
            "surface": items[0]["surface"],
            "location": items[0]["location"],
            "tour": "",
            "start_date": dates[0].strftime("%Y-%m-%d"),
            "end_date": dates[-1].strftime("%Y-%m-%d"),
            "date": dates[0].strftime("%Y-%m-%d")
        })

    output.sort(key=lambda x: x["date"])

    return output


def main():

    matches = load(FULL_DB)

    for y in YEARS:
        data = build(matches, y)
        save(f"{OUT}/{y}.json", data)
        print(f"{y}: {len(data)} tournaments built")


if __name__ == "__main__":
    main()
