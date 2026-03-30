import core_modules

SITECATEGORY_SESSION_URL = "https://api.sitecategory.com/api/session"
SITECATEGORY_CATEGORIZE_URL = "https://api.sitecategory.com/api/categorize"


def _log(msg):
    print(msg, flush=True)


def get_sitecategory_token():
    """Obtain a session token from the sitecategory.com API.

    Returns the token string, or None on failure.
    """
    try:
        response = core_modules.requests.post(
            SITECATEGORY_SESSION_URL,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        token = response.json().get("token")
        _log(f"[sitecategory] Session token obtained")
        return token
    except Exception as e:
        _log(f"[sitecategory] Failed to obtain session token: {e}")
        return None


def get_sitecategory_category(domain, token):
    """Get the URL category for a domain using the sitecategory.com API.

    Returns the category string (e.g. 'Search Engines and Portals') or
    'Unknown' if the category cannot be determined. Never raises.
    """
    if not token:
        _log(f"  [get_sitecategory_category] No token available – using 'Unknown' for {domain}")
        return "Unknown"
    try:
        _log(f"  [get_sitecategory_category] Looking up category for {domain}")
        response = core_modules.requests.post(
            SITECATEGORY_CATEGORIZE_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json={"domain": domain},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        category = data.get("category", "")
        if category:
            _log(f"  [get_sitecategory_category] Category for {domain}: {category}")
            return category
        _log(f"  [get_sitecategory_category] No category returned for {domain} – using 'Unknown'")
        return "Unknown"
    except Exception as e:
        _log(f"  [get_sitecategory_category] Error fetching category for {domain}: {e}")
        return "Unknown"


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

