import json
import re

FILE = "docs/data/golf/pga_winners.json"


def clean(name):
    if not name:
        return ""

    name = str(name)

    # remove brackets
    name = re.sub(r"\s*\(.*?\)", "", name)

    # split multi names
    if "/" in name:
        name = name.split("/")[0]
    if "&" in name:
        name = name.split("&")[0]

    return name.strip()


def main():
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for row in data:
        row["winner"] = clean(row.get("winner", ""))

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Players cleaned")


if __name__ == "__main__":
    main()
