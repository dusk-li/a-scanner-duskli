import core_modules
import core_functions

#Initialise url and xpath query for source code search
pwww_url = 'https://publicwww.com/websites/%22prefers-color-scheme%3A+dark%22/'
pwww_xpath = '//a[contains(@href,"?export=urls")]'

today = core_modules.date.today().isoformat()

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
    num_domains = sum(1 for _ in open('/tmp/downloads/prefers-color-schemedark.txt', 'r'))
    with open('/tmp/downloads/prefers-color-schemedark.txt', 'r') as file:
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
                        if cat.text in banned_sites_data.get('categories', []):
                            print("Category",cat," is in the banned sites data. Skipping.")
                            break
                    else:
                        fname = "/tmp/sites/" + domain + ".txt"
                        print("Success! There are",len(cats), "categories for", domain)
                        contrast = core_functions.chrome_check_contrast(domain)
                        if contrast == 0:
                            print("Domain", domain, "contrast check result: BLOCKED")
                            contrast = "BLOCKED"
                        else:
                            print("Domain", domain, "contrast check result:",contrast)
                
                        # Source list was pulled from a publicwww crawl of sites that contain "prefers-color-scheme: dark"
                        # Hence score of 2 for auto detection 
                        dark_mode_score = 2
                        dark_mode = "Auto"
                        
                        if contrast == "PASS":
                            contrast_score = 1
                        else:
                            contrast_score = 0
                        
                        site_score = dark_mode_score + contrast_score
                        site_cats = ','.join(element.get_text() for element in cats)
                        
                        yaml_string = f'''
---
category: {site_cats}
url: {domain}
dark_mode: {dark_mode}
contrast_accessibility: {contrast}
accessibility_rating: {site_score}/3
last_updated: {today}
'''
                        
                        # Specify the output file path
                        output_file = f'websites/{domain}.yaml'

                        # Write the dictionary to the YAML file
                        with open(output_file, 'w') as yaml_file:
                            yaml_file.write(yaml_string)
                            yaml_file.close()

                        print(f"Dictionary saved as '{output_file}'.")
        
                i = i + 1