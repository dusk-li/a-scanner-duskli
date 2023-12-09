from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse

# Setup options for headless Chrome
options = Options()
options.add_argument("--headless")

# Initialize the Chrome driver
driver = webdriver.Chrome(options=options)

# Retrieve the list of URLs
response = requests.get('https://publicwww.com/websites/%22color-scheme%3Adark%22/?export=urls')
urls = response.text.split('\n')

for url in urls:
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
