import requests

url = "https://afltables.com/motor/bathurst/bathurst_2023.html"

res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

print("STATUS:", res.status_code)
print("LENGTH:", len(res.text))

print(res.text[:500])
