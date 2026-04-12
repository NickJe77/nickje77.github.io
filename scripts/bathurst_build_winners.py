import json
from pathlib import Path

print("BATHURST WINNERS BUILDER (FINAL – NO SCRAPING)")

OUT = Path("docs/data/bathurst/winners.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

data = [

# 1960s
{"year":1960,"drivers":["Frank Coad","John Roxburgh"],"car":"Valiant"},
{"year":1961,"drivers":["Bob Jane","Harry Firth"],"car":"Jaguar"},
{"year":1962,"drivers":["Bob Jane","Harry Firth"],"car":"Jaguar"},
{"year":1963,"drivers":["Harry Firth","Bob Jane"],"car":"Ford Cortina"},
{"year":1964,"drivers":["Bob Jane","George Reynolds"],"car":"Ford Cortina"},
{"year":1965,"drivers":["Barry Seton","Midge Bosworth"],"car":"Ford Cortina"},
{"year":1966,"drivers":["Rauno Aaltonen","Bob Holden"],"car":"Mini Cooper S"},
{"year":1967,"drivers":["Harry Firth","Fred Gibson"],"car":"Ford Falcon GT"},
{"year":1968,"drivers":["Bruce McPhee","Barry Mulholland"],"car":"Holden Monaro"},
{"year":1969,"drivers":["Colin Bond","Tony Roberts"],"car":"Holden Monaro"},
{"year":1970,"drivers":["Allan Moffat"],"car":"Ford Falcon"},
{"year":1971,"drivers":["Allan Moffat"],"car":"Ford Falcon"},
{"year":1972,"drivers":["Peter Brock"],"car":"Holden Torana"},
{"year":1973,"drivers":["Allan Moffat","Ian Geoghegan"],"car":"Ford Falcon"},
{"year":1974,"drivers":["John Goss","Kevin Bartlett"],"car":"Ford Falcon"},
{"year":1975,"drivers":["Peter Brock","Brian Sampson"],"car":"Holden Torana"},
{"year":1976,"drivers":["Bob Morris","John Fitzpatrick"],"car":"Holden Torana"},
{"year":1977,"drivers":["Allan Moffat","Jacky Ickx"],"car":"Ford Falcon"},
{"year":1978,"drivers":["Peter Brock","Jim Richards"],"car":"Holden Torana"},
{"year":1979,"drivers":["Peter Brock","Jim Richards"],"car":"Holden Torana"},

# 1980s
{"year":1980,"drivers":["Peter Brock","Jim Richards"],"car":"Holden Commodore"},
{"year":1981,"drivers":["Dick Johnson","John French"],"car":"Ford Falcon"},
{"year":1982,"drivers":["Peter Brock","Larry Perkins"],"car":"Holden Commodore"},
{"year":1983,"drivers":["John Harvey","Peter Brock","Larry Perkins"],"car":"Holden Commodore"},
{"year":1984,"drivers":["Peter Brock","Larry Perkins"],"car":"Holden Commodore"},
{"year":1985,"drivers":["John Goss","Armin Hahne"],"car":"Jaguar XJ-S"},
{"year":1986,"drivers":["Allan Grice","Graeme Bailey"],"car":"Holden Commodore"},
{"year":1987,"drivers":["Peter McLeod","David Parsons"],"car":"Holden Commodore"},
{"year":1988,"drivers":["Tony Longhurst","Tomas Mezera"],"car":"Ford Sierra"},
{"year":1989,"drivers":["Dick Johnson","John Bowe"],"car":"Ford Sierra"},

# 1990s
{"year":1990,"drivers":["Win Percy","Allan Grice"],"car":"Holden Commodore"},
{"year":1991,"drivers":["Jim Richards","Mark Skaife"],"car":"Nissan Skyline"},
{"year":1992,"drivers":["Mark Skaife","Jim Richards"],"car":"Nissan Skyline"},
{"year":1993,"drivers":["Larry Perkins","Gregg Hansford"],"car":"Holden Commodore"},
{"year":1994,"drivers":["Dick Johnson","John Bowe"],"car":"Ford Falcon"},
{"year":1995,"drivers":["Larry Perkins","Russell Ingall"],"car":"Holden Commodore"},
{"year":1996,"drivers":["Craig Lowndes","Greg Murphy"],"car":"Holden Commodore"},
{"year":1997,"drivers":["Geoff Brabham","David Brabham"],"car":"BMW"},
{"year":1997,"drivers":["Larry Perkins","Russell Ingall"],"car":"Holden Commodore"},
{"year":1998,"drivers":["Rickard Rydell","Jim Richards"],"car":"Volvo"},
{"year":1998,"drivers":["Jason Bright","Steven Richards"],"car":"Ford Falcon"},
{"year":1999,"drivers":["Steven Richards","Greg Murphy"],"car":"Holden Commodore"},

# 2000s+
{"year":2000,"drivers":["Garth Tander","Jason Bargwanna"],"car":"Holden Commodore"},
{"year":2001,"drivers":["Mark Skaife","Tony Longhurst"],"car":"Holden Commodore"},
{"year":2002,"drivers":["Mark Skaife","Jim Richards"],"car":"Holden Commodore"},
{"year":2003,"drivers":["Greg Murphy","Rick Kelly"],"car":"Holden Commodore"},
{"year":2004,"drivers":["Greg Murphy","Rick Kelly"],"car":"Holden Commodore"},
{"year":2005,"drivers":["Mark Skaife","Todd Kelly"],"car":"Holden Commodore"},
{"year":2006,"drivers":["Craig Lowndes","Jamie Whincup"],"car":"Ford Falcon"},
{"year":2007,"drivers":["Craig Lowndes","Jamie Whincup"],"car":"Ford Falcon"},
{"year":2008,"drivers":["Craig Lowndes","Jamie Whincup"],"car":"Ford Falcon"},
{"year":2009,"drivers":["Will Davison","Garth Tander"],"car":"Holden Commodore"},
{"year":2010,"drivers":["Craig Lowndes","Mark Skaife"],"car":"Holden Commodore"},
{"year":2011,"drivers":["Garth Tander","Nick Percat"],"car":"Holden Commodore"},
{"year":2012,"drivers":["Jamie Whincup","Paul Dumbrell"],"car":"Holden Commodore"},
{"year":2013,"drivers":["Mark Winterbottom","Steven Richards"],"car":"Ford Falcon"},
{"year":2014,"drivers":["Chaz Mostert","Paul Morris"],"car":"Ford Falcon"},
{"year":2015,"drivers":["Craig Lowndes","Steven Richards"],"car":"Holden Commodore"},
{"year":2016,"drivers":["Will Davison","Jonathon Webb"],"car":"Holden Commodore"},
{"year":2017,"drivers":["David Reynolds","Luke Youlden"],"car":"Holden Commodore"},
{"year":2018,"drivers":["Craig Lowndes","Steven Richards"],"car":"Holden Commodore"},
{"year":2019,"drivers":["Scott McLaughlin","Alexandre Prémat"],"car":"Ford Mustang"},
{"year":2020,"drivers":["Shane van Gisbergen","Garth Tander"],"car":"Holden Commodore"},
{"year":2021,"drivers":["Chaz Mostert","Lee Holdsworth"],"car":"Holden Commodore"},
{"year":2022,"drivers":["Shane van Gisbergen","Garth Tander"],"car":"Holden Commodore"},
{"year":2023,"drivers":["Shane van Gisbergen","Richie Stanaway"],"car":"Chevrolet Camaro"},
{"year":2024,"drivers":["Brodie Kostecki","Todd Hazelwood"],"car":"Chevrolet Camaro"},
{"year":2025,"drivers":["Matthew Payne","Garth Tander"],"car":"Ford Mustang"}

]

# remove duplicates safely
seen = set()
final = []

for d in data:
    key = (d["year"], tuple(d["drivers"]))
    if key in seen:
        continue
    seen.add(key)
    final.append(d)

final = sorted(final, key=lambda x: x["year"])

with open(OUT, "w") as f:
    json.dump(final, f, indent=2)

print(f"✅ DONE — saved {len(final)} years")
