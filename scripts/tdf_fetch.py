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
# DATA SOURCES (MEN ONLY)
# -----------------------
URLS = {
    "riders": "https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/men/TDF_Riders_History.csv",
    "stages": "https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/men/TDF_Stages_History.csv",
    "rankings": "https://raw.githubusercontent.com/thomascamminady/LeTourDataSet/master/data/men/TDF_All_Rankings_History.csv",
}

# -----------------------
# CONVERT FUNCTION
# -----------------------
def convert(name, url):
    print("Downloading:", name)

    df = pd.read_csv(url)

    print("Rows:", len(df))

    # Convert NaN → None
    df = df.where(pd.notnull(df), None)

    data = df.to_dict(orient="records")

    out_file = f"{OUTPUT}/{name}.json"

    with open(out_file, "w") as f:
        json.dump(data, f)

    print("Saved:", out_file)


# -----------------------
# RUN
# -----------------------
for name, url in URLS.items():
    convert(name, url)

print("TDF DATA COMPLETE")
