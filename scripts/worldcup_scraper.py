import requests
import os
import json
import time
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

WORLD_CUPS = {
    1975: 60793,
    1979: 60806,
    1983: 60832,
    1987: 60847,
    1992: 60979,
    1996: 60981,
    1999: 61046,
    2003: 61124,
    2007: 125929,
    2011: 381449,
    2015: 509587,
    2019: 1144415,
    2023: 1367856
}

# -----------------------------
# GET MATCH IDS (WORKS ON GH)
# -----------------------------
def get_matches(series_id):

    matches = []
    page = 1

    while True:
        url = f"https://stats.espncricinfo.com/ci/engine/series/{series_id}.html?view=results;page={page}"

        res = requests.get(url, headers=HEADERS)
        html = res.text

        found = re.findall(r"/ci/engine/match/(\d+)\.html", html)

        if not found:
            break

        matches.extend(found)

        page += 1
        time.sleep(1)

    return sorted(list(set(matches)))


# -----------------------------
# SCRAPE MATCH (BASIC SAFE)
# -----------------------------
def scrape_match(match_id):

    url = f"https://www.espncricinfo.com/ci/engine/match/{match_id}.html"

    return {
        "match_id": match_id,
        "url": url
    }


# -----------------------------
# MAIN
# -----------------------------
def main():

    for year, series_id in WORLD_CUPS.items():

        print(f"\n--- {year} ---")

        folder = f"docs/data/cricket/world_cups/{year}"
        os.makedirs(folder, exist_ok=True)

        matches = get_matches(series_id)

        print(f"{len(matches)} matches found")

        for match_id in matches:

            file_path = f"{folder}/{match_id}.json"

            # SAFE MODE (DO NOT OVERWRITE)
            if os.path.exists(file_path):
                continue

            try:
                data = scrape_match(match_id)

                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2)

                print(f"Saved {match_id}")

                time.sleep(1)

            except Exception as e:
                print("FAILED:", match_id, e)


if __name__ == "__main__":
    main()
