import json
from pathlib import Path

print("START IPL 2026 BUILD")

INPUT_FILE = Path("docs/data/ipl/ipl_2026_FULL.json")
OUTPUT_FILE = Path("docs/data/ipl/ipl_2026.json")

print("Checking input file:", INPUT_FILE)

if not INPUT_FILE.exists():
    print("❌ FILE DOES NOT EXIST")
    exit()

with open(INPUT_FILE) as f:
    data = json.load(f)

print("Loaded data type:", type(data))

if isinstance(data, list):
    print("Matches found:", len(data))
else:
    print("Single match detected")

# TEMP WRITE TEST
test_output = {
    "season": 2026,
    "test": True
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(test_output, f)

print("✅ TEST FILE WRITTEN:", OUTPUT_FILE)
