import requests
import json
from pathlib import Path

print("🌍 WORLD CUP BUILDER (API VERSION)")

BASE = Path("docs/data/cricket/worldcups")
BASE.mkdir(parents=True, exist_ok=True)

# -----------------------
# ⚠️ GET FREE API KEY
# https://cricapi.com/
# -----------------------
API_KEY = "YOUR_API_KEY_HERE"

URL = f"https://api.cricapi.com/v1/series_info?apikey={API_KEY}&id=9b4b78e0-5f8c-4b62-9e56-0d4b9b9c9a45"

r = requests.get(URL)
data = r.json()

matches = []

if data.get("data"):

    for match in data["data"].get("matchList", []):

        matches.append({
            "match_id": match.get("id"),
            "name": match.get("name"),
            "date": match.get("date"),
            "status": match.get("status"),
            "venue": match.get("venue")
        })

print("Matches found:", len(matches))

# -----------------------
# SAVE
# -----------------------
out_file = BASE / "2023.json"

with open(out_file, "w") as f:
    json.dump(matches, f, indent=2)

print("Saved:", out_file)
