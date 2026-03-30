import core_modules
import core_functions

core_modules.http.client._MAXHEADERS = 1000

today = core_modules.date.today().isoformat()

# Read the banned_sites JSON file
with open("json/banned_sites.json") as banned_sites:
    banned_sites_data = core_modules.json.load(banned_sites)

# ── Collect URLs from all sources ────────────────────────────────────────────

def load_input_file(path="input/input.txt"):
    """Load URLs from the static input file."""
    urls = []
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.rstrip()
                if line:
                    urls.append(line)
    except FileNotFoundError:
        print(f"Input file not found: {path}")
    return urls

def collect_all_urls():
    """Merge URLs from the input file and all remote sources, deduplicating."""
    seen_domains = set()
    all_urls = []

    sources = load_input_file()
    sources += core_functions.fetch_urls_from_tranco(limit=500)
    sources += core_functions.fetch_urls_from_majestic(limit=500)

    for url in sources:
        url = url.rstrip()
        if not core_modules.validators.url(url):
            continue
        domain = core_modules.urlparse(url).netloc
        if domain and domain not in seen_domains:
            seen_domains.add(domain)
            all_urls.append(url)

    return all_urls

# ── Per-domain scan logic ─────────────────────────────────────────────────────

def process_domain(url):
    """Scan a single URL and write a YAML file if it passes all checks."""
    domain = core_modules.urlparse(url).netloc
    scheme = core_modules.urlparse(url).scheme

    symantec_url = "https://sitereview.symantec.com/#/lookup-result/" + domain
    rslt = core_functions.chrome_get_page_content(symantec_url)

    if rslt == -1:
        print(f"Failure getting page content from domain: {domain} – skipping")
        return

    soup = core_modules.BeautifulSoup(rslt, "html.parser")
    cats = soup.find_all("span", class_="clickable-category")

    if len(cats) == 0:
        return

    for cat in cats:
        if cat.text in banned_sites_data.get("categories", []):
            print(f"Category '{cat.text}' is banned. Skipping {domain}.")
            return

    contrast = core_functions.chrome_check_contrast(domain)
    if contrast == 0:
        print(f"Domain {domain} contrast check result: BLOCKED")
        contrast = "BLOCKED"
    else:
        print(f"Domain {domain} contrast check result: {contrast}")

    try:
        response = core_modules.requests.get(f"{scheme}://{domain}", timeout=15)
        response.raise_for_status()
        body = response.text
    except Exception as e:
        print(f"HTTP request failed for {domain}: {e}")
        body = ""

    if "@media (prefers-color-scheme: dark" in body \
            or "@media (prefers-color-scheme:dark" in body:
        dark_mode_score = 1
        dark_mode = "Manual"
    elif "window.matchMedia('(prefers-color-scheme: dark" in body \
            or "window.matchMedia('(prefers-color-scheme:dark" in body:
        dark_mode_score = 2
        dark_mode = "Auto"
    else:
        dark_mode_score = 0
        dark_mode = "None"

    contrast_score = 1 if contrast == "PASS" else 0
    site_score = dark_mode_score + contrast_score
    site_cats = ", ".join(element.get_text() for element in cats)

    yaml_string = (
        f"---\n"
        f"category: {site_cats}\n"
        f"url: {scheme}://{domain}\n"
        f"dark_mode: {dark_mode}\n"
        f"contrast_accessibility: {contrast}\n"
        f"accessibility_rating: {site_score}/3\n"
        f"last_updated: {today}\n"
    )

    output_file = f"websites/{domain}.yaml"
    with open(output_file, "w") as yaml_file:
        yaml_file.write(yaml_string)

    print(f"Saved '{output_file}' ({len(cats)} categories, score {site_score}/3).")

# ── Main ──────────────────────────────────────────────────────────────────────

all_urls = collect_all_urls()
num_domains = len(all_urls)
print(f"Processing {num_domains} unique domains...")

# Process domains in parallel; limit concurrency to avoid overwhelming Chrome
MAX_WORKERS = 5

with core_modules.concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(process_domain, url): url for url in all_urls}
    for i, future in enumerate(core_modules.concurrent.futures.as_completed(futures), start=1):
        url = futures[future]
        domain = core_modules.urlparse(url).netloc
        try:
            future.result()
        except Exception as exc:
            print(f"[{i}/{num_domains}] {domain} generated an exception: {exc}")
        else:
            print(f"[{i}/{num_domains}] Completed: {domain}")
