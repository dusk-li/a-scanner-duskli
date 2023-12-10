import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse

# Setup options for headless Chrome
options = Options()
options.add_argument("--headless")
prefs = {"download.default_directory" : "/tmp/"}
options.add_experimental_option("prefs",prefs)

# Initialize the Chrome driver
driver = webdriver.Chrome(options=options)

pwww_url = 'https://publicwww.com/websites/%22color-scheme%3Adark%22/'
pwww_xpath = '//a[contains(@href,"?export=urls")]'

# Retrieve the list of URLs
try:

    driver.get(pwww_url)

    downloadfile = driver.find_element("xpath",pwww_xpath)

    downloadfile.click()

    time.sleep(5)

    driver.close()

except Exception as e:

    print(e)

driver = webdriver.Chrome(options=options)

with open('/tmp/color-schemedark.txt', 'r') as file:
    for url in file:
        # Parse the domain from the URL
        domain = urlparse(url).netloc

        # Make a request to the Symantec site review page for the domain
        symantec_url = 'https://sitereview.symantec.com/#/lookup-result/' + domain

        # Load the page
        driver.get(symantec_url)

        # Execute JavaScript and get the page content
        page_content = driver.execute_script("return document.documentElement.outerHTML")

        # Print the page content
        print(page_content)

# Close the driver
driver.quit()