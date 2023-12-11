import core_modules
import core_functions

#Initialise url and xpath query for source code search
pwww_url = 'https://publicwww.com/websites/%22color-scheme%3Adark%22/'
pwww_xpath = '//a[contains(@href,"?export=urls")]'

# Get liat of URLs matching source code query
print("Getting sites that have dark mode in source code from publicwww.com")
rslt = core_functions.chrome_download_linked_file(pwww_url,pwww_xpath)

if rslt == 0: #Success
    print("Success!")
    #Loop through URLs in file and get Symantec site categor(ies)y
    
    i = 1
    
    # Open File
    print("Processing domains...")
    with open('/tmp/downloads/color-schemedark.txt', 'r') as file:
        # Loop through URLs in file
        for url in file:
            
            # Get number of domains in file
            num_domains = sum(1 for _ in file)            
            
            # Parse the domain from the URL
            domain = core_modules.urlparse(url).netloc

            print("Processing domain",i,"of",num_domains,":",domain)

            # Setup url for Symantec lookup inc domain to lookup
            symantec_url = 'https://sitereview.symantec.com/#/lookup-result/' + domain

            # Query Symantec
            rslt = core_functions.chrome_get_page_content(symantec_url)
            
            if rslt == -1:
                print("Failure getting page content from domain: ",domain," - EXITING")
                core_modules.sys.exit()
            else:
                fname = "/tmp/sites/" + domain + ".txt"
                print("Success! Writing page content to",fname)
                f = open (fname, 'w')
                f.write(rslt)
                f.close()
                i = i + 1