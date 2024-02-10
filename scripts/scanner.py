import core_modules
import core_functions

#Initialise url and xpath query for source code search
pwww_url = 'https://publicwww.com/websites/%22color-scheme%3A+dark%22/'
pwww_xpath = '//a[contains(@href,"?export=urls")]'

# Get list of URLs matching source code query
print("Getting sites that have dark mode in source code from publicwww.com")
rslt = core_functions.chrome_download_linked_file(pwww_url,pwww_xpath)

if rslt == 0: #Success
    print("Success!")
    #Loop through URLs in file and get Symantec site categor(ies)y
    
    i = 1

    # Read the banned_sites JSON file
    with open("json/banned_sites.json") as banned_sites:
        banned_sites_data = core_modules.json.load(banned_sites)
    
    # Open File
    print("Processing domains...")
    num_domains = sum(1 for _ in open('/tmp/downloads/color-schemedark.txt', 'r'))
    with open('/tmp/downloads/color-schemedark.txt', 'r') as file:
        lines = file.readlines()  # Read all lines into a list
        num_domains = len(lines)  # Get the total number of domains
        for line in lines:
            domain = core_modules.urlparse(line).netloc
            print(f"Processing domain {i} of {num_domains}:", domain)
            # Setup url for Symantec lookup inc domain to lookup
            symantec_url = 'https://sitereview.symantec.com/#/lookup-result/' + domain

            # Query Symantec
            rslt = core_functions.chrome_get_page_content(symantec_url)
                
            if rslt == -1:
                print("Failure getting page content from domain: ",domain," - EXITING")
                core_modules.sys.exit()
            else:
                soup = core_modules.BeautifulSoup(rslt, 'html.parser')
                cats = soup.find_all("span", class_="clickable-category")
                if len(cats) > 0:
                    for cat in cats:
                        if cat in banned_sites_data:
                            print(f"Category '{cat}' is in the banned sites data. Exiting.")
                            break
                    else:
                        fname = "/tmp/sites/" + domain + ".txt"
                        print("Success! There are",len(cats), "categories for", domain)
                        contrast = core_functions.chrome_check_contrast(domain)
                        if contrast == 0:
                            print("Domain", domain, "contrast check result: SCANFAIL")
                        else:
                            print("Domain", domain, "contrast check result:",contrast)
                i = i + 1