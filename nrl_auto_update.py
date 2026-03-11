import json
import requests
from pathlib import Path

SEASON = 2026

INDEX = Path("docs/data/nrl/index.json")
MATCH_DIR = Path(f"docs/data/nrl/matches/{SEASON}")
MATCH_DIR.mkdir(parents=True, exist_ok=True)

URL = f"https://www.nrl.com/draw/data?competition=111&season={SEASON}"

print("Downloading NRL data...")

headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    r = requests.get(URL, headers=headers, timeout=30)
except Exception as e:
    print("Request failed:", e)
    exit()

print("HTTP status:", r.status_code)
print("\n--- RAW RESPONSE START ---\n")
print(r.text[:3000])
print("\n--- RAW RESPONSE END ---\n")

try:
    data = r.json()
except Exception:
    print("Response was not valid JSON.")
    exit()

print("Top-level keys detected:", list(data.keys()))

# Create empty index if it doesn't exist
if INDEX.exists():
    with open(INDEX) as f:
        index = json.load(f)
else:
    index = {"season": SEASON, "games": []}

print("Index currently contains", len(index["games"]), "games")

# We are not parsing yet — only inspecting response
print("\nScript finished (debug mode).")
print("Update complete")
