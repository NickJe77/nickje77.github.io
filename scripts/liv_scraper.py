from pathlib import Path
import json

print("TEST SCRIPT RUNNING")

OUT = Path("docs/data/golf/liv")
OUT.mkdir(parents=True, exist_ok=True)

data = [
    {
        "season": 2026,
        "event": "TEST EVENT",
        "date": "TODAY",
        "location": "TEST",
        "winner": "TEST PLAYER",
        "score": "-10"
    }
]

with open(OUT / "2026.json", "w") as f:
    json.dump(data, f, indent=2)

print("FILE WRITTEN")
