import json
import os

BASE = "docs/data/tennis/seasons"

def load(path):
    if not os.path.exists(path):
        print("❌ Missing:", path)
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def shift_year(date_str, year):
    if not date_str or len(date_str) < 10:
        return date_str
    return year + date_str[4:]

def dedupe(data):
    seen = set()
    out = []

    for t in data:
        key = (t.get("tournament",""), t.get("date",""))
        if key in seen:
            continue
        seen.add(key)
        out.append(t)

    return out

def main():

    source = load(f"{BASE}/2024.json")

    if not source:
        print("❌ 2024.json missing or empty")
        return

    for year in ["2025", "2026"]:

        new = []

        for t in source:
            new.append({
                "tournament": t.get("tournament",""),
                "surface": t.get("surface",""),
                "location": t.get("location",""),
                "tour": t.get("tour",""),
                "start_date": shift_year(t.get("start_date",""), year),
                "end_date": shift_year(t.get("end_date",""), year),
                "date": shift_year(t.get("date",""), year)
            })

        new = dedupe(new)

        save(f"{BASE}/{year}.json", new)
        print(f"✅ Built {year} with {len(new)} tournaments")

if __name__ == "__main__":
    main()
