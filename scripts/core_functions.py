import core_modules

CATEGORY_LOAD_TIMEOUT_MS = 15000


def _log(msg):
    print(msg, flush=True)


def get_page_content(browser, c_url):
    """Fetch rendered page HTML from the given URL using an existing Playwright browser."""
    page = browser.new_page()
    page_content = ""
    try:
        retries = 3
        while retries > 0:
            _log(f"  [get_page_content] goto {c_url} (attempts left: {retries})")
            page.goto(c_url, timeout=30000)
            # Wait for the loading spinner to disappear
            try:
                page.wait_for_selector(".loading-spinner", state="hidden", timeout=20000)
                _log(f"  [get_page_content] spinner gone for {c_url}")
            except core_modules.PlaywrightTimeoutError:
                _log(f"  [get_page_content] spinner still present after attempt {4 - retries}, retrying...")
                retries -= 1
                continue

            # Wait for category results to render before reading the page
            try:
                page.wait_for_selector("span.clickable-category", timeout=CATEGORY_LOAD_TIMEOUT_MS)
                _log(f"  [get_page_content] clickable-category selector found for {c_url}")
            except core_modules.PlaywrightTimeoutError:
                _log(f"  [get_page_content] clickable-category selector NOT found within {CATEGORY_LOAD_TIMEOUT_MS}ms for {c_url} – proceeding anyway")

            page_content = page.inner_html("body")
            _log(f"  [get_page_content] page body length: {len(page_content)} chars")
            break

    except Exception as e:
        _log(f"  [get_page_content] Error fetching page content for {c_url}: {e}")
        return -1
    finally:
        page.close()

    return page_content


def check_contrast(browser, t_url):
    """Check colour contrast for the given domain using an existing Playwright browser."""
    page = browser.new_page()
    try:
        _log(f"  [check_contrast] Checking contrast for {t_url}")
        page.goto("https://color.a11y.com/Contrast/", timeout=30000)
        page.fill('[name="urltotest"]', t_url)
        page.click('[name="submitbutton"]')

        # Wait for results to appear
        try:
            page.wait_for_selector(".congratsbox, .nocongratsbox", timeout=20000)
            _log(f"  [check_contrast] Result selector found for {t_url}")
        except core_modules.PlaywrightTimeoutError:
            _log(f"  [check_contrast] Result selector NOT found within 20s for {t_url} – proceeding anyway")

        page_content = page.inner_html("body")
        soup = core_modules.BeautifulSoup(page_content, "html.parser")
        failed = soup.find_all("div", class_="nocongratsbox")
        passed = soup.find_all("div", class_="congratsbox")

        _log(f"  [check_contrast] {t_url}: passed={len(passed)}, failed={len(failed)}")

        if len(failed) > 0:
            return "FAIL"
        if len(passed) > 0:
            return "PASS"

    except Exception as e:
        _log(f"  [check_contrast] Error checking contrast for {t_url}: {e}")
        return -1
    finally:
        page.close()

    return 0


def fetch_urls_from_tranco(limit=500):
    """Fetch the top `limit` URLs from the Tranco Top-1M list."""
    tranco_url = "https://tranco-list.eu/top-1m.csv.zip"
    urls = []
    try:
        _log(f"Fetching Tranco Top-1M list (top {limit} entries)...")
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
        _log(f"Fetched {len(urls)} URLs from Tranco.")
    except Exception as e:
        _log(f"Failed to fetch Tranco list: {e}")
    return urls


def fetch_urls_from_majestic(limit=500):
    """Fetch the top `limit` URLs from the Majestic Million list."""
    majestic_url = "https://downloads.majestic.com/majestic_million.csv"
    urls = []
    try:
        _log(f"Fetching Majestic Million list (top {limit} entries)...")
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
        _log(f"Fetched {len(urls)} URLs from Majestic Million.")
    except Exception as e:
        _log(f"Failed to fetch Majestic Million list: {e}")
    return urls

