import core_modules
import core_functions
import glob as _glob

core_modules.http.client._MAXHEADERS = 1000

# Flush stdout immediately so CI logs appear in real-time
def log(msg):
    print(msg, flush=True)

today = core_modules.date.today().isoformat()

log(f"Scanner started on {today}")

# Path to the checked-out data repository (set by the workflow)
DATA_REPO_PATH = core_modules.os.environ.get("DATA_REPO_PATH", "../dusk-li-data")

# Maximum number of URLs to process in a single run
MAX_URLS_PER_RUN = 100

# Skip domains already scanned within this many days
RESCAN_AFTER_DAYS = 90

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
        log(f"Loaded {len(urls)} URLs from {path}")
    except FileNotFoundError:
        log(f"Input file not found: {path}")
    return urls


def is_recently_scanned(domain, days=RESCAN_AFTER_DAYS):
    """Return True if the domain was scanned less than `days` days ago."""
    yaml_path = core_modules.os.path.join(DATA_REPO_PATH, "websites", f"{domain}.yaml")
    if not core_modules.os.path.exists(yaml_path):
        return False
    try:
        with open(yaml_path, "r") as f:
            for line in f:
                if line.startswith("last_updated:"):
                    date_str = line.split(":", 1)[1].strip()
                    last_updated = core_modules.datetime.date.fromisoformat(date_str)
                    age = (core_modules.datetime.date.today() - last_updated).days
                    return age < days
    except (ValueError, OSError) as e:
        log(f"Warning: could not read last_updated for {domain}: {e}")
    return False


def collect_all_urls():
    """Merge URLs from the input file and all remote sources, deduplicating.

    Domains already scanned within RESCAN_AFTER_DAYS are skipped.
    The final list is capped at MAX_URLS_PER_RUN entries.
    """
    seen_domains = set()
    all_urls = []

    sources = load_input_file()
    sources += core_functions.fetch_urls_from_tranco(limit=500)
    sources += core_functions.fetch_urls_from_majestic(limit=500)

    log(f"Total raw URLs from all sources: {len(sources)}")

    skipped = 0
    invalid = 0
    duplicates = 0
    for url in sources:
        url = url.rstrip()
        if not core_modules.validators.url(url):
            invalid += 1
            continue
        domain = core_modules.urlparse(url).netloc
        if not domain or domain in seen_domains:
            duplicates += 1
            continue
        seen_domains.add(domain)
        if is_recently_scanned(domain):
            skipped += 1
            continue
        all_urls.append(url)

    log(f"URL filtering: {invalid} invalid, {duplicates} duplicates, {skipped} recently scanned, {len(all_urls)} remaining")

    if skipped:
        log(f"Skipped {skipped} domain(s) scanned within the last {RESCAN_AFTER_DAYS} days.")

    if len(all_urls) > MAX_URLS_PER_RUN:
        log(f"Capping URL list from {len(all_urls)} to {MAX_URLS_PER_RUN}.")
        all_urls = all_urls[:MAX_URLS_PER_RUN]

    return all_urls

# ── Per-domain scan logic ─────────────────────────────────────────────────────

def process_domain(url):
    """Scan a single URL and write a YAML file if it passes all checks."""
    domain = core_modules.urlparse(url).netloc
    scheme = core_modules.urlparse(url).scheme

    log(f"[{domain}] Starting scan...")

    log(f"[{domain}] Running contrast check...")
    contrast = core_functions.check_contrast(url)

    if contrast == 0:
        log(f"[{domain}] Contrast check result: BLOCKED (no result from checker)")
        contrast = "BLOCKED"
    else:
        log(f"[{domain}] Contrast check result: {contrast}")

    try:
        response = core_modules.requests.get(f"{scheme}://{domain}", timeout=15)
        response.raise_for_status()
        body = response.text
        log(f"[{domain}] HTTP fetch succeeded ({len(body)} bytes)")
    except Exception as e:
        log(f"[{domain}] HTTP request failed: {e}")
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

    yaml_string = (
        f"---\n"
        f"url: {scheme}://{domain}\n"
        f"dark_mode: {dark_mode}\n"
        f"contrast_accessibility: {contrast}\n"
        f"accessibility_rating: {site_score}/3\n"
        f"last_updated: {today}\n"
    )

    output_file = f"websites/{domain}.yaml"
    with open(output_file, "w") as yaml_file:
        yaml_file.write(yaml_string)

    log(f"[{domain}] Saved '{output_file}' (dark_mode: {dark_mode}, score: {site_score}/3)")

# ── Main ──────────────────────────────────────────────────────────────────────

all_urls = collect_all_urls()
num_domains = len(all_urls)
log(f"Processing {num_domains} unique domains...")

# Process domains in parallel; limit concurrency to avoid overwhelming resources
MAX_WORKERS = 5

with core_modules.concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(process_domain, url): url for url in all_urls}
    for i, future in enumerate(core_modules.concurrent.futures.as_completed(futures), start=1):
        url = futures[future]
        domain = core_modules.urlparse(url).netloc
        try:
            future.result()
        except Exception as exc:
            log(f"[{i}/{num_domains}] {domain} generated an exception: {exc}")
        else:
            log(f"[{i}/{num_domains}] Completed: {domain}")

# Report how many YAML files were produced
yaml_files = _glob.glob("websites/*.yaml")
log(f"Scan complete. {len(yaml_files)} YAML file(s) written to websites/")
