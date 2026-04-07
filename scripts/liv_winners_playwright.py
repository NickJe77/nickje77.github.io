from playwright.sync_api import sync_playwright

print("LIV API DEBUG")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    def log_response(response):
        try:
            url = response.url
            if "liv" in url.lower():
                print("API:", url)
        except:
            pass

    page.on("response", log_response)

    page.goto("https://www.livgolf.com/schedule?season=2024",
              wait_until="domcontentloaded",
              timeout=120000)

    page.wait_for_timeout(10000)

    browser.close()
