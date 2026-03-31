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

# Maximum number of new (not-yet-in-data-repo) URLs to scan per run
SCAN_LIMIT = 500

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


def is_in_data_repo(domain):
    """Return True if the domain already has a YAML file in dusk-li-data."""
    yaml_path = core_modules.os.path.join(DATA_REPO_PATH, "websites", f"{domain}.yaml")
    return core_modules.os.path.exists(yaml_path)


def collect_all_urls():
    """Merge URLs from all sources, deduplicating.

    Sources: static input file, Tranco top-500, Majestic top-500.
    Domains already present in dusk-li-data are skipped.
    Returns at most SCAN_LIMIT URLs.
    """
    seen_domains = set()
    all_urls = []

    sources = load_input_file()
    sources += core_functions.fetch_urls_from_tranco(limit=5000)
    sources += core_functions.fetch_urls_from_majestic(limit=5000)

    log(f"Total raw URLs from all sources: {len(sources)}")

    skipped = 0
    invalid = 0
    duplicates = 0
    for url in sources:
        url = url.rstrip()
        if not core_modules.validators.url(url):
            invalid += 1
            continue
        domain = core_modules.urlparse(url).hostname
        if not domain or domain in seen_domains:
            duplicates += 1
            continue
        seen_domains.add(domain)
        if is_in_data_repo(domain):
            skipped += 1
            continue
        all_urls.append(url)
        if len(all_urls) >= SCAN_LIMIT:
            break

    log(f"URL filtering: {invalid} invalid, {duplicates} duplicates, {skipped} already in data repo, {len(all_urls)} collected" + (" (limit reached)" if len(all_urls) >= SCAN_LIMIT else ""))

    return all_urls

# ── Per-domain scan logic ─────────────────────────────────────────────────────

def process_domain(url):
    """Scan a single URL and write a YAML file if it passes all checks."""
    parsed = core_modules.urlparse(url)
    domain = parsed.hostname  # hostname only (no port) — matches YAML filenames
    scheme = parsed.scheme

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

FORCE_URL = core_modules.os.environ.get("FORCE_URL", "").strip()

if FORCE_URL:
    # Single-URL forced scan (e.g. triggered by a review request issue).
    # Bypasses is_in_data_repo() so re-reviews always run.
    log(f"FORCE_URL set — scanning {FORCE_URL} only.")
    if not core_modules.validators.url(FORCE_URL):
        log(f"FORCE_URL '{FORCE_URL}' is not a valid URL. Exiting.")
        raise SystemExit(1)
    process_domain(FORCE_URL)
else:
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
