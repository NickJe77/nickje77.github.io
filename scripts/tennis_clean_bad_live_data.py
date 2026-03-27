import json
import re
from pathlib import Path

SEASONS_DIR = Path("docs/data/tennis/seasons")


def clean_text(v):
    return re.sub(r"\s+", " ", str(v or "")).strip()


def is_time_text(value):
    return bool(re.fullmatch(r"\d{1,2}:\d{2}", clean_text(value)))


def is_bad_row(row):
    p1 = clean_text(row.get("player1"))
    p2 = clean_text(row.get("player2"))
    score = clean_text(row.get("score"))
    rnd = clean_text(row.get("round"))

    if not p1 or not p2:
        return True
    if p2.lower() == "info":
        return True
    if score.lower() == "info":
        return True
    if is_time_text(rnd):
        return True
    return False


for year_file in [SEASONS_DIR / "2025.json", SEASONS_DIR / "2026.json"]:
    if not year_file.exists():
        print(f"Missing {year_file}")
        continue

    data = json.loads(year_file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print(f"Skipping non-list file {year_file}")
        continue

    before = len(data)
    cleaned = [row for row in data if isinstance(row, dict) and not is_bad_row(row)]
    after = len(cleaned)

    year_file.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{year_file.name}: {before} -> {after}")
