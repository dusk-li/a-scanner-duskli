import core_modules

CATEGORIFY_API_URL = "https://categorify.org/api"


def _log(msg):
    print(msg, flush=True)


def get_categorify_category(domain):
    """Get the URL category for a domain using the categorify.org API.

    Returns a comma-separated category string (e.g. 'Search Engine, Clean Browsing')
    or 'Unknown' if the category cannot be determined.  Never raises; all errors are
    handled internally so callers can always expect a string back.
    """
    try:
        _log(f"  [get_categorify_category] Looking up category for {domain}")
        response = core_modules.requests.get(
            CATEGORIFY_API_URL,
            params={"website": domain},
            timeout=15,
        )
        if response.status_code == 400:
            _log(f"  [get_categorify_category] Invalid domain or unprocessable: {domain} – using 'Unknown'")
            return "Unknown"
        response.raise_for_status()
        data = response.json()
        categories = data.get("category", [])
        if categories:
            result = ", ".join(categories)
            _log(f"  [get_categorify_category] Category for {domain}: {result}")
            return result
        _log(f"  [get_categorify_category] No category returned for {domain} – using 'Unknown'")
        return "Unknown"
    except Exception as e:
        _log(f"  [get_categorify_category] Error fetching category for {domain}: {e}")
        return "Unknown"


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

