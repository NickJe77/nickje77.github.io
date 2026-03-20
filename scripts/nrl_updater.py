from pathlib import Path
import json

print("TEST WRITE START")

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "docs/data/nrl/matches/TEST.json"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

data = {
    "status": "THIS FILE WAS WRITTEN",
    "test": 123
}

with open(OUTPUT, "w") as f:
    json.dump(data, f, indent=2)

print("WROTE FILE TO:", OUTPUT.resolve())
print("TEST COMPLETE")
