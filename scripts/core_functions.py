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

        core_modules.time.sleep(5)

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
