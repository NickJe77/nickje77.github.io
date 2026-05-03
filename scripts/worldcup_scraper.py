import requests
from bs4 import BeautifulSoup
import os

HEADERS = {"User-Agent": "Mozilla/5.0"}

# test ONE known working match (your example)
TEST_ID = 67

def run():

    url = f"https://www.howstat.com/Cricket/Statistics/Matches/MatchScoreCard_ODI.asp?MatchCode={TEST_ID:04d}"

    print("URL:", url)

    res = requests.get(url, headers=HEADERS)

    print("STATUS:", res.status_code)
    print("LENGTH:", len(res.text))

    # print first 500 chars so we SEE what we got
    print("\nPAGE START:\n")
    print(res.text[:500])

    soup = BeautifulSoup(res.text, "lxml")

    tables = soup.find_all("table")

    print("\nTABLES FOUND:", len(tables))

    # dump one table so we can inspect structure
    if tables:
        print("\nFIRST TABLE SAMPLE:\n")
        print(str(tables[0])[:500])


if __name__ == "__main__":
    run()
