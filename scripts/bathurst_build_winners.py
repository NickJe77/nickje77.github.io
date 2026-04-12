import requests
import json
import re
from pathlib import Path

print("BATHURST WINNERS BUILDER (API FIX)")

OUT = Path("docs/data/bathurst/winners.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

URL = "https://en.wikipedia.org/w/api.php"

params = {
    "action": "parse",
    "page": "Bathurst 1000",
    "format": "json",
    "prop": "text",
}

def clean(x):
    if not x:
        return None
    x = re.sub(r"\[[^\]]+\]", "", x)
    x = x.replace("\xa0", " ")
    return re.sub(r"\s+", " ", x).strip()

def split_drivers(text):
    if not text:
        return []

    text = clean(text)

    parts = re.split(r"/| and ", text)
    parts = [p.strip() for p in parts if p.strip()]

    # fallback split
    if len(parts) == 1:
        words = parts[0].split()
        if len(words) >= 4:
            mid = len(words) // 2
            parts = [
                " ".join(words[:mid]),
                " ".join(words[mid:])
            ]

    return parts

print("Fetching via API...")
res = requests.get(URL, params=params)
data = res.json()

html = data["parse"]["text"]["*"]

# 🔥 find the winners table directly in HTML string
tables = re.findall(r"<table.*?wikitable.*?>.*?</table>", html, re.DOTALL)

target = None

for t in tables:
    if "List of winners" in html or "Drivers" in t:
        target = t
        break

if target is None:
    raise Exception("No winners table found")

# 🔥 extract rows
rows = re.findall(r"<tr>(.*?)</tr>", target, re.DOTALL)

results = []

for row in rows:
    cols = re.findall(r"<td.*?>(.*?)</td>", row, re.DOTALL)

    if len(cols) < 3:
        continue

    try:
        year_text = clean(cols[0])
        match = re.search(r"\d{4}", year_text or "")
        if not match:
            continue

        year = int(match.group())

        if year < 1960 or year > 2100:
            continue

        drivers_raw = clean(cols[1])
        car = clean(cols[2])

        drivers = split_drivers(drivers_raw)

        results.append({
            "year": year,
            "drivers": drivers,
            "car": car
        })

    except:
        continue

results = sorted(results, key=lambda x: x["year"])

with open(OUT, "w") as f:
    json.dump(results, f, indent=2)

print(f"✅ DONE — saved {len(results)} years")
