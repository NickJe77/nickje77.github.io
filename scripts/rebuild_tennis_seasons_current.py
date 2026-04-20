import json
import os

BASE = "docs/data/tennis/seasons"

def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def build_year(source, year):

    seen = set()
    output = []

    day = 1

    for t in source:

        name = t.get("tournament","")

        if not name or name in seen:
            continue

        seen.add(name)

        # stagger dates so UI works properly
        date = f"{year}-01-{str(day).zfill(2)}"

        output.append({
            "tournament": name,
            "surface": t.get("surface",""),
            "location": t.get("location",""),
            "tour": t.get("tour",""),
            "start_date": date,
            "end_date": date,
            "date": date
        })

        day += 1
        if day > 28:
            day = 1

    return output


def main():

    source = load(f"{BASE}/2024.json")

    if not source:
        print("❌ 2024 missing")
        return

    for year in ["2025", "2026"]:
        data = build_year(source, year)
        save(f"{BASE}/{year}.json", data)
        print(year, len(data))


if __name__ == "__main__":
    main()
