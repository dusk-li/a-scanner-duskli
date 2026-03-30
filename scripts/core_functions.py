import core_modules


def _log(msg):
    print(msg, flush=True)


def check_contrast(url):
    """Check colour contrast and accessibility for the given URL using pa11y.

    Returns 'PASS' if no WCAG2AA errors are found, 'FAIL' if errors exist,
    or -1 on a technical failure (pa11y crash / timeout).
    """
    try:
        _log(f"  [check_contrast] Running pa11y for {url}")
        result = core_modules.subprocess.run(
            [
                "pa11y",
                "--reporter", "json",
                "--standard", "WCAG2AA",
                "--chromium-flag", "--no-sandbox",
                "--chromium-flag", "--disable-setuid-sandbox",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        # pa11y exit codes: 0 = clean, 1 = issues found, 2 = technical error
        if result.returncode == 2:
            _log(f"  [check_contrast] pa11y technical error for {url}: {result.stderr.strip()}")
            return -1

        issues = core_modules.json.loads(result.stdout) if result.stdout.strip() else []
        errors = [i for i in issues if i.get("type") == "error"]
        _log(f"  [check_contrast] {url}: {len(errors)} WCAG2AA error(s) ({len(issues)} total issue(s))")
        return "FAIL" if errors else "PASS"

    except core_modules.subprocess.TimeoutExpired:
        _log(f"  [check_contrast] pa11y timed out for {url}")
        return -1
    except Exception as e:
        _log(f"  [check_contrast] Error checking accessibility for {url}: {e}")
        return -1


def fetch_urls_from_data_repo(data_repo_path):
    """Return URLs for all domains already in the data repo.

    These are candidates for rescan — the is_recently_scanned filter in
    collect_all_urls() will exclude any scanned within RESCAN_AFTER_DAYS.
    """
    urls = []
    websites_dir = core_modules.os.path.join(data_repo_path, "websites")
    if not core_modules.os.path.isdir(websites_dir):
        _log(f"Data repo websites dir not found: {websites_dir}")
        return urls
    try:
        for fname in core_modules.os.listdir(websites_dir):
            if not fname.endswith(".yaml"):
                continue
            domain = fname[:-5]  # strip .yaml
            urls.append(f"https://{domain}/")
        _log(f"Found {len(urls)} URLs in data repo for rescan consideration.")
    except Exception as e:
        _log(f"Failed to read data repo: {e}")
    return urls


def fetch_urls_from_tranco(limit=500):
    """Fetch the top `limit` URLs from the Tranco Top-1M list."""
    tranco_url = "https://tranco-list.eu/top-1m.csv.zip"
    urls = []
    try:
        _log(f"Fetching Tranco Top-1M list (top {limit} entries)...")
        response = core_modules.requests.get(tranco_url, timeout=60)
        response.raise_for_status()
        with core_modules.zipfile.ZipFile(core_modules.io.BytesIO(response.content)) as z:
            csv_filename = z.namelist()[0]
            with z.open(csv_filename) as csv_file:
                reader = core_modules.csv.reader(core_modules.io.TextIOWrapper(csv_file, encoding="utf-8"))
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    if len(row) >= 2:
                        domain = row[1].strip()
                        urls.append(f"https://{domain}/")
        _log(f"Fetched {len(urls)} URLs from Tranco.")
    except Exception as e:
        _log(f"Failed to fetch Tranco list: {e}")
    return urls


def fetch_urls_from_majestic(limit=500):
    """Fetch the top `limit` URLs from the Majestic Million list."""
    majestic_url = "https://downloads.majestic.com/majestic_million.csv"
    urls = []
    try:
        _log(f"Fetching Majestic Million list (top {limit} entries)...")
        response = core_modules.requests.get(majestic_url, timeout=60)
        response.raise_for_status()
        reader = core_modules.csv.DictReader(
            core_modules.io.StringIO(response.text)
        )
        for i, row in enumerate(reader):
            if i >= limit:
                break
            domain = row.get("Domain", "").strip()
            if domain:
                urls.append(f"https://{domain}/")
        _log(f"Fetched {len(urls)} URLs from Majestic Million.")
    except Exception as e:
        _log(f"Failed to fetch Majestic Million list: {e}")
    return urls

