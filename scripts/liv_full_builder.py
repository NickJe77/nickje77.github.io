import requests
import json
from pathlib import Path
import time

print("=== LIV FULL BUILDER (API) ===")

# 🔑 YOUR KEY (already seen in your screenshot)
API_KEY = "ad73e6aa34d346e29e241f57dc92cabe"

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

SEASONS = [2022, 2023, 2024, 2025, 2026]

BASE = "https://api.sportsdata.io/golf/v2/json/Tournaments"

HEADERS = {
    "Ocp-Apim-Subscription-Key": API_KEY
}


def get_events(year):
    url = f"{BASE}/{year}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)

        print(f"{year} STATUS:", r.status_code)

        if r.status_code != 200:
            print("FAILED:", r.text[:200])
            return []

        return r.json()

    except Exception as e:
        print("ERROR:", e)
        return []


def build(events, year):
    output = []

    for e in events:
        name = e.get("Name", "")

        # only LIV events
        if "LIV" not in name:
            continue

        output.append({
            "season": year,
            "event": name,
            "date": e.get("StartDate", ""),
            "location": e.get("City", ""),
            "winner": "",
            "score": ""
        })

    return output


all_events = []

for year in SEASONS:
    print(f"\n--- Processing {year} ---")

    events = get_events(year)

    print(f"{year} TOTAL EVENTS:", len(events))

    data = build(events, year)

    print(f"{year} LIV EVENTS:", len(data))

    # write yearly file
    with open(OUT / f"{year}.json", "w") as f:
        json.dump(data, f, indent=2)

    all_events.extend(data)

    time.sleep(1)


# write master file
with open(OUT / "all.json", "w") as f:
    json.dump(all_events, f, indent=2)

print("\n=== DONE ===")
print("TOTAL LIV EVENTS:", len(all_events))
