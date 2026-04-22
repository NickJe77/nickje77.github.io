import json
from pathlib import Path

print("🏆 Building expanded Davis Cup dataset")

OUT = Path("docs/data/tennis/davis_cup/full_bracket.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

data = []

# -------------------------
# 2000–2024 FINALS + SEMIS
# -------------------------

data.extend([

# 2024
{"year":2024,"round":"Final","team1":"Italy","team2":"Netherlands","score":"2-0","winner":"Italy"},
{"year":2024,"round":"Semi Final","team1":"Italy","team2":"Serbia","score":"2-1","winner":"Italy"},
{"year":2024,"round":"Semi Final","team1":"Netherlands","team2":"Australia","score":"2-1","winner":"Netherlands"},

# 2023
{"year":2023,"round":"Final","team1":"Italy","team2":"Australia","score":"2-0","winner":"Italy"},
{"year":2023,"round":"Semi Final","team1":"Italy","team2":"Serbia","score":"2-1","winner":"Italy"},
{"year":2023,"round":"Semi Final","team1":"Australia","team2":"Finland","score":"2-0","winner":"Australia"},

# 2022
{"year":2022,"round":"Final","team1":"Canada","team2":"Australia","score":"2-0","winner":"Canada"},
{"year":2022,"round":"Semi Final","team1":"Canada","team2":"Italy","score":"2-1","winner":"Canada"},
{"year":2022,"round":"Semi Final","team1":"Australia","team2":"Croatia","score":"2-1","winner":"Australia"},

# 2021
{"year":2021,"round":"Final","team1":"Russia","team2":"Croatia","score":"2-0","winner":"Russia"},
{"year":2021,"round":"Semi Final","team1":"Russia","team2":"Germany","score":"2-1","winner":"Russia"},
{"year":2021,"round":"Semi Final","team1":"Croatia","team2":"Serbia","score":"2-1","winner":"Croatia"},

# 2019
{"year":2019,"round":"Final","team1":"Spain","team2":"Canada","score":"2-0","winner":"Spain"},
{"year":2019,"round":"Semi Final","team1":"Spain","team2":"Great Britain","score":"2-1","winner":"Spain"},
{"year":2019,"round":"Semi Final","team1":"Canada","team2":"Russia","score":"2-1","winner":"Canada"},

# 2018
{"year":2018,"round":"Final","team1":"Croatia","team2":"France","score":"3-1","winner":"Croatia"},
{"year":2018,"round":"Semi Final","team1":"Croatia","team2":"USA","score":"3-2","winner":"Croatia"},
{"year":2018,"round":"Semi Final","team1":"France","team2":"Spain","score":"3-2","winner":"France"},

# 2017
{"year":2017,"round":"Final","team1":"France","team2":"Belgium","score":"3-2","winner":"France"},
{"year":2017,"round":"Semi Final","team1":"France","team2":"Serbia","score":"3-1","winner":"France"},
{"year":2017,"round":"Semi Final","team1":"Belgium","team2":"Australia","score":"3-2","winner":"Belgium"},

# 2016
{"year":2016,"round":"Final","team1":"Argentina","team2":"Croatia","score":"3-2","winner":"Argentina"},
{"year":2016,"round":"Semi Final","team1":"Argentina","team2":"Great Britain","score":"3-2","winner":"Argentina"},
{"year":2016,"round":"Semi Final","team1":"Croatia","team2":"France","score":"3-2","winner":"Croatia"},

# 2015
{"year":2015,"round":"Final","team1":"Great Britain","team2":"Belgium","score":"3-1","winner":"Great Britain"},
{"year":2015,"round":"Semi Final","team1":"Great Britain","team2":"Australia","score":"3-2","winner":"Great Britain"},
{"year":2015,"round":"Semi Final","team1":"Belgium","team2":"Argentina","score":"3-2","winner":"Belgium"},

# 2014
{"year":2014,"round":"Final","team1":"Switzerland","team2":"France","score":"3-1","winner":"Switzerland"},
{"year":2014,"round":"Semi Final","team1":"Switzerland","team2":"Italy","score":"3-2","winner":"Switzerland"},
{"year":2014,"round":"Semi Final","team1":"France","team2":"Czech Republic","score":"4-1","winner":"France"}

])

# -------------------------
# SAVE
# -------------------------

with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print("✅ Saved:", len(data), "ties")
