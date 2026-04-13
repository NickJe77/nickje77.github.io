import csv
from pathlib import Path
import re
from collections import defaultdict

print("CLEANING BATHURST DATASET")

INPUT = Path("docs/data/bathurst/raw/bathurst_full.csv")
OUTPUT = Path("docs/data/bathurst/raw/bathurst_clean.csv")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def clean(x):
    if not x:
        return ""
    x = str(x)
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x


# 🔥 BETTER NAME EXTRACTION
def extract_names(text):
    text = clean(text)

    # find proper names (First Last)
    names = re.findall(r"[A-Z][a-z]+ [A-Z][a-z]+", text)

    # filter junk
    bad_words = ["Motors", "Ford", "Team", "Co", "Ltd", "Holden", "Nissan"]

    out = []
    for n in names:
        if any(b.lower() in n.lower() for b in bad_words):
            continue
        if n not in out:
            out.append(n)

    return out[:2]


rows_by_year = defaultdict(list)

# LOAD
with open(INPUT, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        year = int(row["year"])
        finish = int(row["finish"])

        raw_text = f"{row.get('driver1','')} {row.get('driver2','')}"

        names = extract_names(raw_text)

        if len(names) == 1:
            names.append("Unknown")

        if len(names) < 2:
            continue

        rows_by_year[year].append({
            "year": year,
            "finish": finish,
            "driver1": names[0],
            "driver2": names[1],
            "car": clean(row.get("car", ""))
        })


# 🔥 REMOVE DUPLICATE FINISHES (CRITICAL FIX)
clean_rows = []

for year, rows in rows_by_year.items():

    by_finish = {}

    for r in rows:
        f = r["finish"]

        if f not in by_finish:
            by_finish[f] = r
            continue

        # prefer row with no "Unknown"
        if "Unknown" in by_finish[f]["driver2"] and "Unknown" not in r["driver2"]:
            by_finish[f] = r

    year_rows = list(by_finish.values())
    year_rows.sort(key=lambda x: x["finish"])

    clean_rows.extend(year_rows)


# SORT FINAL
clean_rows.sort(key=lambda x: (x["year"], x["finish"]))


# WRITE
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["year", "finish", "driver1", "driver2", "car"]
    )
    writer.writeheader()
    writer.writerows(clean_rows)

print(f"🔥 DONE — {len(clean_rows)} clean rows written")
