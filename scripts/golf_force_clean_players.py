import json
import re

FILE = "docs/data/golf/pga_winners.json"


def clean(name):
    if not name:
        return ""

    # force string
    name = str(name)

    # remove weird unicode spaces
    name = name.replace("\xa0", " ")

    # remove brackets (2), (3), (a)
    name = re.sub(r"\s*\(.*?\)", "", name)

    # remove asterisks
    name = name.replace("*", "")

    # split multiple names
    for sep in [" / ", "/", " & ", "&", " and "]:
        if sep in name:
            name = name.split(sep)[0]

    # normalize spacing
    name = re.sub(r"\s+", " ", name).strip()

    # kill junk
    if name.lower() in ["not played", "-", "—", "nan", "none", ""]:
        return ""

    return name


def main():
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = 0

    for row in data:
        old = row.get("winner", "")
        new = clean(old)

        if old != new:
            row["winner"] = new
            changed += 1

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Force cleaned {changed} rows")


if __name__ == "__main__":
    main()
