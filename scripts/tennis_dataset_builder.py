import os
import json
import requests
import zipfile
import io
import csv
import datetime

OUTPUT_DIR = "docs/data/tennis/matches"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ATP_URL = "https://github.com/JeffSackmann/tennis_atp/archive/refs/heads/master.zip"
WTA_URL = "https://github.com/JeffSackmann/tennis_wta/archive/refs/heads/master.zip"

TMP_DIR = "tennis_tmp"

# 🔥 IMPORTANT: STOP AT LAST COMPLETE YEAR
CURRENT_YEAR = datetime.datetime.now().year - 1  # e.g. 2025 → builds to 2024


# -----------------------------
# CLEAN TEMP
# -----------------------------
def clean_tmp():
    if os.path.exists(TMP_DIR):
        for root, dirs, files in os.walk(TMP_DIR, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
    else:
        os.makedirs(TMP_DIR)


# -----------------------------
# DOWNLOAD + EXTRACT
# -----------------------------
def download_zip(url):
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(TMP_DIR)


# -----------------------------
# LOAD CSV
# -----------------------------
def load_csv(path, gender):

    matches = []

    if not os.path.exists(path):
        return matches

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            if not row.get("winner_name") or not row.get("loser_name"):
                continue

            matches.append({
                "tournament": row.get("tourney_name"),
                "surface": row.get("surface"),
                "round": row.get("round"),
                "player1": row.get("winner_name"),
                "player2": row.get("loser_name"),
                "score": row.get("score"),
                "date": row.get("tourney_date"),
                "gender": gender
            })

    return matches


# -----------------------------
# BUILD YEAR
# -----------------------------
def build_year(year):

    print(f"\nProcessing {year}")

    atp_path = f"{TMP_DIR}/tennis_atp-master/atp_matches_{year}.csv"
    wta_path = f"{TMP_DIR}/tennis_wta-master/wta_matches_{year}.csv"

    matches = []

    matches += load_csv(atp_path, "M")
    matches += load_csv(wta_path, "W")

    if not matches:
        print(f"{year} missing")
        return

    output_path = f"{OUTPUT_DIR}/{year}.json"

    json.dump(matches, open(output_path, "w"), indent=2)

    print(f"{year} done ({len(matches)} matches)")


# -----------------------------
# MAIN
# -----------------------------
def main():

    clean_tmp()

    print("Downloading ATP dataset...")
    download_zip(ATP_URL)

    print("Downloading WTA dataset...")
    download_zip(WTA_URL)

    # 🔥 BUILD HISTORY ONLY
    for year in range(1968, CURRENT_YEAR):
        build_year(year)

    print("\nDone building historical dataset.")


if __name__ == "__main__":
    main()
