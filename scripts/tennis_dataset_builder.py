import os
import json
import requests
import zipfile
import io
import csv

OUTPUT_DIR = "docs/data/tennis/matches"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATA_URL = "https://github.com/JeffSackmann/tennis_atp/archive/refs/heads/master.zip"


def download_dataset():
    print("Downloading dataset...")
    r = requests.get(DATA_URL)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall("tennis_data")


def build_year(year):
    path = f"tennis_data/tennis_atp-master/atp_matches_{year}.csv"

    if not os.path.exists(path):
        print(f"{year} missing")
        return

    matches = []

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
                "date": row["tourney_date"]
            })

    json.dump(
        matches,
        open(f"{OUTPUT_DIR}/{year}.json", "w"),
        indent=2
    )

    print(f"{year} done ({len(matches)} matches)")


def main():
    download_dataset()

    for year in range(1968, 2027):
        build_year(year)


if __name__ == "__main__":
    main()
