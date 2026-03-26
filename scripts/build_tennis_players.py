import os
import json
import requests
import zipfile
import io
import csv

OUTPUT_DIR = "docs/data/tennis/matches"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ATP_URL = "https://github.com/JeffSackmann/tennis_atp/archive/refs/heads/master.zip"
WTA_URL = "https://github.com/JeffSackmann/tennis_wta/archive/refs/heads/master.zip"


def download_and_extract(url, folder):
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(folder)


def load_year(path, gender):
    matches = []

    if not os.path.exists(path):
        return matches

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            matches.append({
                "tournament": row["tourney_name"],
                "surface": row["surface"],
                "round": row["round"],
                "player1": row["winner_name"],
                "player2": row["loser_name"],
                "score": row["score"],
                "date": row["tourney_date"],
                "gender": gender
            })

    return matches


def main():

    print("Downloading ATP...")
    download_and_extract(ATP_URL, "tennis_data")

    print("Downloading WTA...")
    download_and_extract(WTA_URL, "tennis_data")

    for year in range(1968, 2027):

        print(f"Processing {year}")

        atp_path = f"tennis_data/tennis_atp-master/atp_matches_{year}.csv"
        wta_path = f"tennis_data/tennis_wta-master/wta_matches_{year}.csv"

        matches = []

        matches += load_year(atp_path, "M")
        matches += load_year(wta_path, "W")

        if not matches:
            print(f"{year} missing")
            continue

        json.dump(
            matches,
            open(f"{OUTPUT_DIR}/{year}.json", "w"),
            indent=2
        )

        print(f"{year} done ({len(matches)} matches)")


if __name__ == "__main__":
    main()
