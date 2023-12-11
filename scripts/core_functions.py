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

        driver.close()

    except Exception as e:

        print(e)
        
        return -1
    
    return 0

def chrome_get_page_content(c_url):
    # Setup options for headless Chrome
    options = core_modules.Options()
    options.add_argument("--headless")
    options.add_argument("--enable-javascript")
    prefs = {"download.default_directory" : "/tmp/downloads/"}
    options.add_experimental_option("prefs",prefs)

    # Initialize the Chrome driver
    driver = core_modules.webdriver.Chrome(options=options)
    try:
        driver.implicitly_wait(10)
        
        driver.get(c_url)
        
        core_modules.time.sleep(10)

        # Execute JavaScript and get the page content
        page_content = driver.execute_script("return document.body.innerHTML")

        driver.close()

    except Exception as e:

        print(e)
        
        return -1
    
    return page_content