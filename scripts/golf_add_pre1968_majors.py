import requests
from bs4 import BeautifulSoup
import json

URL = "https://thegolfnewsnet.com/list-of-mens-golf-major-championship-winners-by-year/"

OUTPUT_FILE = "docs/data/golf/pga_winners.json"

MAJORS = ["Masters", "U.S. Open", "The Open Championship", "PGA Championship"]

def normalise_event(name):
    if "Masters" in name:
        return "Masters Tournament"
    if "U.S." in name:
        return "U.S. Open"
    if "Open Championship" in name:
        return "The Open Championship"
    if "PGA Championship" in name:
        return "PGA Championship"
    return name

def load_existing():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def scrape():
    res = requests.get(URL)
    soup = BeautifulSoup(res.text, "html.parser")

    tables = soup.find_all("table")

    results = []

    for table in tables:
        rows = table.find_all("tr")

        for r in rows[1:]:
            cols = [c.get_text(strip=True) for c in r.find_all("td")]

            if len(cols) < 5:
                continue

            year = cols[0]

            if not year.isdigit():
                continue

            year = int(year)

            masters = cols[1]
            us_open = cols[2]
            open_champ = cols[3]
            pga = cols[4]

            data = [
                ("Masters Tournament", masters),
                ("U.S. Open", us_open),
                ("The Open Championship", open_champ),
                ("PGA Championship", pga)
            ]

            for event, winner in data:

                if not winner or winner.lower() in ["—", "-", ""]:
                    continue

                # skip amateur / weird formatting cleanup
                winner = winner.replace("*", "").strip()

                results.append({
                    "tour": "pga",
                    "year": year,
                    "event": event,
                    "winner": winner,
                    "major": True,
                    "score": "",
                    "venue": "",
                    "country": ""
                })

    return results

def main():
    existing = load_existing()

    existing_keys = set((e["event"], e["year"]) for e in existing)

    new_data = scrape()

    added = []

    for row in new_data:
        if row["year"] >= 1968:
            continue

        key = (row["event"], row["year"])

        if key in existing_keys:
            continue

        added.append(row)

    combined = existing + added

    combined.sort(key=lambda x: (x["event"], x["year"]))

    save(combined)

    print(f"Added {len(added)} pre-1968 major results")

if __name__ == "__main__":
    main()
