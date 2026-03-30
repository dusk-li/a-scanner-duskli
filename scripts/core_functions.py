import core_modules


def get_page_content(browser, c_url):
    """Fetch rendered page HTML from the given URL using an existing Playwright browser."""
    page = browser.new_page()
    page_content = ""
    try:
        retries = 3
        while retries > 0:
            page.goto(c_url, timeout=30000)
            # Wait for the loading spinner to disappear
            try:
                page.wait_for_selector(".loading-spinner", state="hidden", timeout=20000)
            except core_modules.PlaywrightTimeoutError:
                print(f"Spinner still present after attempt {4 - retries}")
                retries -= 1
                continue

            page_content = page.inner_html("body")
            break

    except Exception as e:
        print(f"Error fetching page content for {c_url}: {e}")
        return -1
    finally:
        page.close()

    return page_content


def check_contrast(browser, t_url):
    """Check colour contrast for the given domain using an existing Playwright browser."""
    page = browser.new_page()
    try:
        page.goto("https://color.a11y.com/Contrast/", timeout=30000)
        page.fill('[name="urltotest"]', t_url)
        page.click('[name="submitbutton"]')

        # Wait for results to appear
        try:
            page.wait_for_selector(".congratsbox, .nocongratsbox", timeout=20000)
        except core_modules.PlaywrightTimeoutError:
            pass

        page_content = page.inner_html("body")
        soup = core_modules.BeautifulSoup(page_content, "html.parser")
        failed = soup.find_all("div", class_="nocongratsbox")
        passed = soup.find_all("div", class_="congratsbox")

        if len(failed) > 0:
            return "FAIL"
        if len(passed) > 0:
            return "PASS"

    except Exception as e:
        print(f"Error checking contrast for {t_url}: {e}")
        return -1
    finally:
        page.close()

    return 0


def fetch_urls_from_tranco(limit=500):
    """Fetch the top `limit` URLs from the Tranco Top-1M list."""
    tranco_url = "https://tranco-list.eu/top-1m.csv.zip"
    urls = []
    try:
        print(f"Fetching Tranco Top-1M list (top {limit} entries)...")
        response = core_modules.requests.get(tranco_url, timeout=60)
        response.raise_for_status()
        with core_modules.zipfile.ZipFile(core_modules.io.BytesIO(response.content)) as z:
            csv_filename = z.namelist()[0]
            with z.open(csv_filename) as csv_file:
                reader = core_modules.csv.reader(core_modules.io.TextIOWrapper(csv_file, encoding="utf-8"))
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    if len(row) >= 2:
                        domain = row[1].strip()
                        urls.append(f"https://{domain}/")
        print(f"Fetched {len(urls)} URLs from Tranco.")
    except Exception as e:
        print(f"Failed to fetch Tranco list: {e}")
    return urls


def fetch_urls_from_majestic(limit=500):
    """Fetch the top `limit` URLs from the Majestic Million list."""
    majestic_url = "https://downloads.majestic.com/majestic_million.csv"
    urls = []
    try:
        print(f"Fetching Majestic Million list (top {limit} entries)...")
        response = core_modules.requests.get(majestic_url, timeout=60)
        response.raise_for_status()
        reader = core_modules.csv.DictReader(
            core_modules.io.StringIO(response.text)
        )
        for i, row in enumerate(reader):
            if i >= limit:
                break
            domain = row.get("Domain", "").strip()
            if domain:
                urls.append(f"https://{domain}/")
        print(f"Fetched {len(urls)} URLs from Majestic Million.")
    except Exception as e:
        print(f"Failed to fetch Majestic Million list: {e}")
    return urls

