import pandas as pd
import json
import os

print("TDF DATA FETCH STARTED")

# -----------------------
# OUTPUT LOCATION
# -----------------------
OUTPUT = "docs/data/cycling"
os.makedirs(OUTPUT, exist_ok=True)

# -----------------------
# DATA SOURCES (MEN ONLY - FIXED URLS)
# -----------------------
URLS = {
    "riders": "https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/main/data/men/TDF_Riders_History.csv",
    "stages": "https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/main/data/men/TDF_Stages_History.csv",
    "rankings": "https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/main/data/men/TDF_All_Rankings_History.csv",
}

# -----------------------
# DOWNLOAD + CONVERT
# -----------------------
def convert(name, url):
    print("\n-----------------------")
    print("Downloading:", name)
    print("URL:", url)

    try:
        df = pd.read_csv(url)
    except Exception as e:
        print("❌ FAILED:", name)
        print("ERROR:", e)
        return

    print("✅ Loaded rows:", len(df))

    # Replace NaN with None
    df = df.where(pd.notnull(df), None)

    data = df.to_dict(orient="records")

    out_file = f"{OUTPUT}/{name}.json"

    try:
        with open(out_file, "w") as f:
            json.dump(data, f)
        print("✅ Saved:", out_file)
    except Exception as e:
        print("❌ SAVE FAILED:", out_file)
        print("ERROR:", e)


# -----------------------
# RUN ALL
# -----------------------
for name, url in URLS.items():
    convert(name, url)

print("\nTDF DATA COMPLETE")
