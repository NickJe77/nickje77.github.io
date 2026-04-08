import json
import re

FILE = "docs/data/golf/pga_winners.json"

MAJORS = [
    "Masters Tournament",
    "U.S. Open",
    "The Open Championship",
    "PGA Championship"
]

def clean(name):
    if not name:
        return ""
    name = re.sub(r"\s*\(.*?\)", "", name)
    return name.strip()


# ✅ ONLY DATA WE ADD (SAFE RANGE)
US_OPEN = {
    1895:"Horace Rawlins",1896:"James Foulis",1897:"Joe Lloyd",1898:"Fred Herd",
    1899:"Willie Smith",1900:"Harry Vardon",1901:"Willie Anderson",
    1902:"Laurie Auchterlonie",1903:"Willie Anderson",1904:"Willie Anderson",
    1905:"Willie Anderson",1906:"Alex Smith",1907:"Alex Ross",
    1908:"Fred McLeod",1909:"George Sargent",1910:"Alex Smith",
    1911:"John McDermott",1912:"John McDermott",1913:"Francis Ouimet",
    1914:"Walter Hagen"
}

MASTERS = {
    1934:"Horton Smith",1935:"Gene Sarazen",1936:"Horton Smith",
    1937:"Byron Nelson",1938:"Henry Picard",1939:"Ralph Guldahl",
    1940:"Jimmy Demaret",1941:"Craig Wood",1942:"Byron Nelson",
    1946:"Herman Keiser",1947:"Jimmy Demaret",1948:"Claude Harmon",
    1949:"Sam Snead",1950:"Jimmy Demaret",1951:"Ben Hogan",
    1952:"Sam Snead",1953:"Ben Hogan",1954:"Sam Snead",
    1955:"Cary Middlecoff",1956:"Jack Burke Jr.",1957:"Doug Ford",
    1958:"Arnold Palmer",1959:"Art Wall Jr.",1960:"Arnold Palmer",
    1961:"Gary Player",1962:"Arnold Palmer",1963:"Jack Nicklaus",
    1964:"Arnold Palmer",1965:"Jack Nicklaus",1966:"Jack Nicklaus",
    1967:"Gay Brewer"
}

OPEN = {
    1860:"Willie Park Sr.",1861:"Old Tom Morris",1862:"Old Tom Morris",
    1863:"Willie Park Sr.",1864:"Old Tom Morris",1865:"Andrew Strath",
    1866:"Willie Park Sr.",1867:"Old Tom Morris",1868:"Young Tom Morris",
    1869:"Young Tom Morris",1870:"Young Tom Morris",1872:"Young Tom Morris",
    1873:"Tom Kidd",1874:"Mungo Park",1875:"Willie Park Sr.",
    1876:"Bob Martin",1877:"Jamie Anderson",1878:"Jamie Anderson",
    1879:"Jamie Anderson",1880:"Bob Ferguson",1881:"Bob Ferguson",
    1882:"Bob Ferguson",1883:"Willie Fernie",1884:"Jack Simpson",
    1885:"Bob Martin",1886:"David Brown",1887:"Willie Park Jr.",
    1888:"Jack Burns",1889:"Willie Park Jr.",1890:"John Ball",
    1891:"Hugh Kirkaldy",1892:"Harold Hilton",1893:"Willie Auchterlonie",
    1894:"J.H. Taylor",1895:"J.H. Taylor",1896:"Harry Vardon",
    1897:"Harold Hilton",1898:"Harry Vardon",1899:"Harry Vardon",
    1900:"J.H. Taylor",1901:"James Braid",1902:"Sandy Herd",
    1903:"Harry Vardon",1904:"Jack White",1905:"James Braid",
    1906:"James Braid",1907:"Arnaud Massy",1908:"James Braid",
    1909:"J.H. Taylor",1910:"James Braid",1911:"Harry Vardon",
    1912:"Ted Ray",1913:"J.H. Taylor",1914:"J.H. Taylor"
}

PGA = {
    1916:"Jim Barnes",1919:"Jim Barnes",1920:"Jock Hutchison",
    1921:"Walter Hagen",1922:"Gene Sarazen",1923:"Gene Sarazen",
    1924:"Walter Hagen",1925:"Walter Hagen",1926:"Walter Hagen",
    1927:"Walter Hagen",1928:"Leo Diegel",1929:"Leo Diegel",
    1930:"Tommy Armour",1931:"Tom Creavy",1932:"Olin Dutra",
    1933:"Gene Sarazen",1934:"Paul Runyan",1935:"Johnny Revolta",
    1936:"Denny Shute",1937:"Denny Shute",1938:"Paul Runyan",
    1939:"Henry Picard",1940:"Byron Nelson",1941:"Vic Ghezzi",
    1942:"Sam Snead",1944:"Bob Hamilton",1945:"Byron Nelson",
    1946:"Ben Hogan",1947:"Jim Ferrier",1948:"Ben Hogan",
    1949:"Sam Snead",1950:"Chandler Harper",1951:"Sam Snead",
    1952:"Jim Turnesa",1953:"Walter Burkemo",1954:"Chick Harbert",
    1955:"Doug Ford",1956:"Jack Burke Jr.",1957:"Lionel Hebert",
    1958:"Dow Finsterwald",1959:"Bob Rosburg",1960:"Jay Hebert",
    1961:"Jerry Barber",1962:"Gary Player",1963:"Jack Nicklaus",
    1964:"Bobby Nichols",1965:"Dave Marr",1966:"Al Geiberger",
    1967:"Don January"
}


def main():
    with open(FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing = set((d["event"], d["year"]) for d in data)

    added = 0

    def add(event, year, winner):
        nonlocal added
        key = (event, year)

        if key in existing:
            return

        data.append({
            "tour":"pga",
            "year":year,
            "event":event,
            "winner":clean(winner),
            "major":True,
            "score":"",
            "venue":"",
            "country":""
        })

        added += 1

    for y,w in US_OPEN.items():
        add("U.S. Open", y, w)

    for y,w in MASTERS.items():
        add("Masters Tournament", y, w)

    for y,w in OPEN.items():
        add("The Open Championship", y, w)

    for y,w in PGA.items():
        add("PGA Championship", y, w)

    data.sort(key=lambda x:(x["event"], x["year"]))

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Added {added} missing majors safely")


if __name__ == "__main__":
    main()
