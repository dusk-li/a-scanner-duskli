from requests_html import HTMLSession
from pathlib import Path
import requests
import wget
import time
import sys
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Retrieve the list of URLs
#session = HTMLSession()
#response = session.get('https://publicwww.com/websites/%22color-scheme%3Adark%22/?export=urls')
#response.html.render(wait=2,sleep=45)
fileurl = 'https://publicwww.com/websites/%22color-scheme%3Adark%22/?export=urls'
wget.download(fileurl, 'urls.txt')
#print(response.status_code)
urls = Path('urls.txt').read_text()
#urls = urls.split('\n')
print(urls)
sys.exit()
for url in urls:
    # Parse the domain from the URL
    domain = urlparse(url).netloc
    
    # Make a request to the Symantec site review page for the domain
    symantec_url = 'https://sitereview.symantec.com/#/lookup-result/' + domain
    symantec_response = requests.get(symantec_url)

    # Parse the page content
    soup = BeautifulSoup(symantec_response.text, 'html.parser')

    # Print the page content
    print(soup.prettify())
    
    # Wait random number of seconds between 1 and 45 to avoid triggering bot protection
    import random
    random_integer = random.randint(0, 10)
    time.sleep(random_integer)
    