import requests
import json
from pathlib import Path

print("PARIS 2024 MEDAL SCRAPER")

OUTPUT = Path("docs/data/olympics/paris_2024.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# -----------------------------------
# REAL API (used by olympics.com)
# -----------------------------------
API = "https://olympics.com/api/v1/results/sport"

sports = [
    "athletics",
    "swimming",
    "basketball",
    "football",
    "tennis",
    "cycling",
    "rowing",
    "boxing",
    "judo",
    "wrestling"
]

all_events = []

for sport in sports:
    print("Fetching:", sport)

    try:
        url = f"{API}?sport={sport}&edition=paris-2024&noc=all"
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            print("Failed:", sport)
            continue

        data = r.json()

        for event in data.get("events", []):

            medals = {
                "gold": [],
                "silver": [],
                "bronze": []
            }

            for result in event.get("results", []):
                medal = result.get("medal")

                name = result.get("athlete", {}).get("name") or result.get("team", {}).get("name")

                if not name:
                    continue

                if medal == "GOLD":
                    medals["gold"].append(name)
                elif medal == "SILVER":
                    medals["silver"].append(name)
                elif medal == "BRONZE":
                    medals["bronze"].append(name)

            if medals["gold"] or medals["silver"] or medals["bronze"]:
                all_events.append({
                    "year": 2024,
                    "sport": event.get("sport"),
                    "event": event.get("name"),
                    **medals
                })

    except Exception as e:
        print("Error:", sport, e)


print("Total events:", len(all_events))


# -----------------------------------
# SAVE
# -----------------------------------
with open(OUTPUT, "w") as f:
    json.dump(all_events, f, indent=2)

print("DONE ✅")
