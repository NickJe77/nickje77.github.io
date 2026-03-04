#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path("docs/data/nba")

def main():
    if not ROOT.exists():
        print("No docs/data/nba folder found.")
        return

    seasons = sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name.isdigit()], key=lambda p: int(p.name))
    if not seasons:
        print("No season folders found under docs/data/nba")
        return

    for sdir in seasons:
        files = [p for p in sdir.glob("*.json") if p.name != "index.json"]
        if not files:
            continue

        dates = []
        for p in files:
            try:
                d = json.load(open(p, "r", encoding="utf-8"))
                dt = d.get("date", "")
                if dt:
                    dates.append(dt)
            except Exception:
                pass

        dates.sort()
        print(f"{sdir.name}: games={len(files)}  earliest={dates[0] if dates else '??'}  latest={dates[-1] if dates else '??'}")

if __name__ == "__main__":
    main()
