import pandas as pd
import json
import re

EXCEL = "scripts/golf.xlsx"
FILE = "docs/data/golf/pga_winners.json"

def clean(name):
    if not name:
        return ""
    name = str(name)
    name = re.sub(r"\s*\(.*?\)", "", name)
    return name.strip()

def main():
    df = pd.read_excel(EXCEL)
    df.columns = ["year", "masters", "pga", "us_open", "open"]

    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    added = 0

    for _, row in df.iterrows():
        year = int(row["year"])

        mapping = {
            "Masters Tournament": clean(row["masters"]),
            "PGA Championship": clean(row["pga"]),
            "U.S. Open": clean(row["us_open"]),
            "The Open Championship": clean(row["open"])
        }

        for event, winner in mapping.items():

            found = False

            for d in data:
                if d["event"] == event and d["year"] == year:
                    if d.get("winner") != winner:
                        d["winner"] = winner
                        updated += 1
                    found = True
                    break

            if not found:
                data.append({
                    "tour": "pga",
                    "year": year,
                    "event": event,
                    "winner": winner,
                    "major": True,
                    "score": "",
                    "venue": "",
                    "country": ""
                })
                added += 1

    data.sort(key=lambda x: (x["event"], x["year"]))

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Updated {updated} rows, added {added} rows")

if __name__ == "__main__":
    main()gold
