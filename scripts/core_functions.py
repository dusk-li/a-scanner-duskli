import core_modules
    
def chrome_get_page_content(c_url):
    ua = core_modules.UserAgent()
    userAgent = ua.random
    options = core_modules.Options()
    options.add_argument('--headless')
    options.add_argument(f'--user-agent={userAgent}')
    prefs = {"download.default_directory": "/tmp/downloads/"}
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--enable-javascript")

    # Initialize the Chrome driver
    driver = core_modules.webdriver.Chrome(options=options)
    try:
        driver.implicitly_wait(5)
        retries = 3
        while retries > 0:
            driver.get(c_url)
            # Wait for page load and spinner to disappear, up to 15 seconds
            try:
                core_modules.WebDriverWait(driver, 15).until(
                    core_modules.EC.invisibility_of_element_located((core_modules.By.CLASS_NAME, "loading-spinner"))
                )
            except core_modules.TimeoutException:
                print(f"Spinner still present after attempt {4 - retries}")
                retries -= 1
                continue

            # Execute JavaScript and get the page content
            page_content = driver.execute_script("return document.body.innerHTML")
            soup = core_modules.BeautifulSoup(page_content, 'html.parser')
            spinner = soup.find_all("div", class_="loading-spinner ng-star-inserted")
            if spinner:
                print(f"Spinner found after attempt {4 - retries}")
                retries -= 1
            else:
                break

        driver.quit()

    except Exception as e:
        print(e)
        return -1

    return page_content

def chrome_check_contrast(t_url):
    # Setup options for headless Chrome
    options = core_modules.Options()
    options.add_argument("--headless")
    prefs = {"download.default_directory" : "/tmp/downloads/"}
    options.add_experimental_option("prefs",prefs)

    # Initialize the Chrome driver
    driver = core_modules.webdriver.Chrome(options=options)
    try:
        driver.get("https://color.a11y.com/Contrast/")

        input_field = driver.find_element(core_modules.By.NAME, "urltotest")
        
        input_field.send_keys(t_url)

        check_button = driver.find_element(core_modules.By.NAME, "submitbutton")

        check_button.click()

        # Wait for results to appear instead of a fixed sleep
        try:
            core_modules.WebDriverWait(driver, 15).until(
                lambda d: len(d.find_elements(core_modules.By.CLASS_NAME, "congratsbox")) > 0 or
                          len(d.find_elements(core_modules.By.CLASS_NAME, "nocongratsbox")) > 0
            )
        except core_modules.TimeoutException:
            pass

        page_content = driver.execute_script("return document.body.innerHTML")
        soup = core_modules.BeautifulSoup(page_content, 'html.parser')
        failed = soup.find_all("div", class_="nocongratsbox")
        passed = soup.find_all("div", class_="congratsbox")
        driver.quit()
        
        if len(failed) > 0:
            return "FAIL"
        if len(passed) > 0:
            return "PASS"

    except Exception as e:

        print(e)
        
        return -1
    
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

