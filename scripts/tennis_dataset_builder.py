import os
import json
import requests
import zipfile
import io
import csv
import datetime
import shutil

OUTPUT_DIR = "docs/data/tennis/matches"
TMP_DIR = "tennis_tmp"

ATP_URL = "https://github.com/JeffSackmann/tennis_atp/archive/refs/heads/master.zip"
WTA_URL = "https://github.com/JeffSackmann/tennis_wta/archive/refs/heads/master.zip"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🔥 CRITICAL: STOP AT LAST COMPLETE YEAR
CURRENT_YEAR = datetime.datetime.now().year - 1   # e.g. 2026 → builds to 2025 EXCLUDED


# -----------------------------
# CLEAN TEMP FOLDER ONLY
# -----------------------------
def clean_tmp():
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR, exist_ok=True)


# -----------------------------
# DOWNLOAD ZIP
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
# BUILD YEAR (HISTORICAL ONLY)
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

    # 🔥 SAFE WRITE — DOES NOT DELETE OTHER YEARS
    with open(output_path, "w") as f:
        json.dump(matches, f, indent=2)

    print(f"{year} done ({len(matches)} matches)")


# -----------------------------
# MAIN
# -----------------------------
def main():

    print("Starting historical build...")

    clean_tmp()

    print("Downloading ATP dataset...")
    download_zip(ATP_URL)

    print("Downloading WTA dataset...")
    download_zip(WTA_URL)

    # 🔥 CRITICAL FIX — DO NOT TOUCH 2025+
    for year in range(1968, CURRENT_YEAR):
        build_year(year)

    print("\n✅ Historical dataset complete (1968 → 2024)")
    print("🚫 2025+ handled by live scraper only")


if __name__ == "__main__":
    main()
