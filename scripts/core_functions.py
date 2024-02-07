import core_modules
    
def chrome_download_linked_file(c_url,c_xpath):
    # Setup options for headless Chrome
    options = core_modules.Options()
    options.add_argument("--headless")
    prefs = {"download.default_directory" : "/tmp/downloads/"}
    options.add_experimental_option("prefs",prefs)

    # Initialize the Chrome driver
    driver = core_modules.webdriver.Chrome(options=options)
    try:
        driver.get(c_url)

        downloadfile = driver.find_element("xpath",c_xpath)

        downloadfile.click()

        core_modules.time.sleep(5)

        driver.quit()

    except Exception as e:

        print(e)
        
        return -1
    
    return 0

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
            core_modules.time.sleep(5)
            driver.refresh()

            # Wait for the spinner to disappear (timeout after 10 seconds)
            try:
                core_modules.WebDriverWait(driver, 10).until(
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

def get_domains_from_file(file_path):
    with open(file_path, 'r') as file:
        return [core_modules.urlparse(line).netloc for line in file]

def check_categories(cats, banned_sites_data):
    banned_categories = set(banned_sites_data)
    for i, domain in enumerate(cats, start=1):
        print(f"Processing domain {i} of {len(cats)}:", domain)
        symantec_url = f"https://sitereview.symantec.com/#/lookup-result/{domain}"
        rslt = chrome_get_page_content(symantec_url)
        if rslt == -1:
            raise ValueError(f"Failure getting page content from domain: {domain}")
        soup = core_modules.BeautifulSoup(rslt, 'html.parser')
        cats = soup.find_all("span", class_="clickable-category")
        if any(cat.text in banned_categories for cat in cats):
            print(f"Category found for domain {domain}. Exiting.")
            break
    else:
        print("No matching categories found. Continue processing.")
