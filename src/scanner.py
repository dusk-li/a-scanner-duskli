from requests_html import HTMLSession
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Retrieve the list of URLs
session = HTMLSession()
response = session.get('https://publicwww.com/websites/%22color-scheme%3Adark%22/?export=urls')
response.html.render(wait=2,sleep=3)
print(response.status_code)
urls = response.text.split('\n')
exit
for url in urls:
    # Parse the domain from the URL
    domain = urlparse(url).netloc
    
    # Make a request to the Symantec site review page for the domain
    sweb_url = 'https://www.similarweb.com/website/' + domain
    sweb_response = requests.get(sweb_url)

    # Parse the page content
    soup = BeautifulSoup(sweb_response.text, 'html.parser')

    # Print the page content
    print(soup.prettify())
    
    # Wait random number of seconds between 1 and 45 to avoid triggering bot protection
    import random
    random_integer = random.randint(0, 10)
    time.sleep(random_integer)
    