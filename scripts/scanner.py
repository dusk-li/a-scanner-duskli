import core_modules
import core_functions

core_functions.chrome_init()

pwww_url = 'https://publicwww.com/websites/%22color-scheme%3Adark%22/'
pwww_xpath = '//a[contains(@href,"?export=urls")]'

core_functions.chrome_download_linked_file(pwww_url,pwww_xpath)
driver.quit()

with open('/tmp/downloads/color-schemedark.txt', 'r') as file:
    for url in file:
        # Parse the domain from the URL
        domain = urlparse(url).netloc

        # Make a request to the Symantec site review page for the domain
        symantec_url = 'https://sitereview.symantec.com/#/lookup-result/' + domain

        core_functions.chrome_init()
        
        driver.get(symantec_url)

        # Execute JavaScript and get the page content
        page_content = driver.execute_script("return document.documentElement.outerHTML")

        # Print the page content
        print(page_content)