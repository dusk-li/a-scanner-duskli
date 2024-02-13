import core_modules
import core_functions

today = core_modules.date.today().isoformat()

i = 1

# Read the banned_sites JSON file
with open("json/banned_sites.json") as banned_sites:
    banned_sites_data = core_modules.json.load(banned_sites)

# Open File
print("Processing domains...")
num_domains = sum(1 for _ in open('input/input.txt', 'r'))
with open('input/input.txt', 'r') as file:
    lines = file.readlines()  # Read all lines into a list
    num_domains = len(lines)  # Get the total number of domains
    for line in lines:
        urlvalidation = core_modules.validators.url(line.rstrip())
        if urlvalidation:
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
                            print("Category",cat.text," is in the banned sites data. Skipping.")
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
                        scheme = core_modules.urlparse(line).scheme
                        url = core_modules.urlparse(line).netloc
                        response = core_modules.requests.get(f"{scheme}://{url}")
                        
                        if response.text.find("@media (prefers-color-scheme: dark") \
                            or response.text.find("@media (prefers-color-scheme:dark"):
                            dark_mode_score = 1    
                            dark_mode = "Manual"
                        
                        if response.text.find("window.matchMedia('(prefers-color-scheme: dark") \
                            or response.text.find("window.matchMedia('(prefers-color-scheme:dark"):
                            dark_mode_score = 2    
                            dark_mode = "Auto"
                        
                        if not response.text.find("prefers-color-scheme: dark") \
                            or not response.text.find("prefers-color-scheme:dark"):
                            dark_mode_score = 0    
                            dark_mode = "None"
                                                                        
                        if contrast == "PASS":
                            contrast_score = 1
                        else:
                            contrast_score = 0
                        
                        site_score = dark_mode_score + contrast_score
                        site_cats = ', '.join(element.get_text() for element in cats)
                        
                        yaml_string = (
                        f"---\n"
                        f"category: {site_cats}\n"
                        f"url: {scheme}://{domain}\n"
                        f"dark_mode: {dark_mode}\n"
                        f"contrast_accessibility: {contrast}\n"
                        f"accessibility_rating: {site_score}/3\n"
                        f"last_updated: {today}\n"
                        )
                        
                        # Specify the output file path
                        output_file = f'websites/{domain}.yaml'

                        # Write the dictionary to the YAML file
                        with open(output_file, 'w') as yaml_file:
                            yaml_file.write(yaml_string)
                            yaml_file.close()

                        print(f"Dictionary saved as '{output_file}'.")
        
                i = i + 1
        else:
            print("Skipping Invalid URL:", line)
            break