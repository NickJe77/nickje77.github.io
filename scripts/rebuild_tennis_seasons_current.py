import json
import os

BASE = "docs/data/tennis/seasons"

SOURCE_YEAR = "2024"
TARGET_YEARS = ["2025", "2026"]

def load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def shift_year(date_str, new_year):
    if not date_str or len(date_str) < 10:
        return date_str
    return new_year + date_str[4:]

def main():
    source_path = f"{BASE}/{SOURCE_YEAR}.json"
    source = load(source_path)

    if not source:
        print("❌ 2024 season missing")
        return

    for year in TARGET_YEARS:
        new_data = []

        for t in source:
            new_data.append({
                "tournament": t.get("tournament",""),
                "surface": t.get("surface",""),
                "location": t.get("location",""),
                "tour": t.get("tour",""),
                "start_date": shift_year(t.get("start_date",""), year),
                "end_date": shift_year(t.get("end_date",""), year),
                "date": shift_year(t.get("date",""), year)
            })

        save(f"{BASE}/{year}.json", new_data)
        print(f"✅ Built {year} with {len(new_data)} tournaments")

if __name__ == "__main__":
    main()
