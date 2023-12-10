def chrome_init():
    # Setup options for headless Chrome
    options = Options()
    options.add_argument("--headless")
    prefs = {"download.default_directory" : "/tmp/downloads/"}
    options.add_experimental_option("prefs",prefs)

    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=options)
    
def chrome_download_linked_file(c_url,c_xpath):
    try:
        driver.get(c_url)

        downloadfile = driver.find_element("xpath",c_xpath)

        downloadfile.click()

        time.sleep(5)

        driver.close()

    except Exception as e:

        print(e)