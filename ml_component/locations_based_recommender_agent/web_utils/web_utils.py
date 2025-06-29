from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Optional
import re
# At first run you will need to install browser binaries: playwright install
from playwright.sync_api import sync_playwright
from typing import Optional
import requests

def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.text
"""
def fetch_html(url: str, timeout: int = 10000) -> Optional[str]:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/114.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                viewport={"width": 1280, "height": 800},
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "DNT": "1",  # Do Not Track
                    "Upgrade-Insecure-Requests": "1"
                }
            )

            page = context.new_page()
            page.goto(url, timeout=timeout)
            page.wait_for_load_state("networkidle")
            content = page.content()

            browser.close()
            return content

    except Exception as e:
        print(f"[ERROR] Failed to fetch HTML from {url}: {e}")
        return None
"""


def extract_text_from_html(html: str) -> str:
    """Extract visible text from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for script_or_style in soup(["script", "style", "noscript"]):
        script_or_style.decompose()
    text = soup.get_text(strip=True)
    return re.sub(r"\s+", " ", text)

def extract_links_from_html(html: str, base_url: str) -> List[str]:
    """Extract and normalize internal links from a page."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("#") or "javascript:" in href:
            continue
        absolute = urljoin(base_url, href)
        if is_internal_url(absolute, base_url):
            links.add(clean_url(absolute))
    return list(links)

def clean_url(url: str) -> str:
    """Remove tracking parameters and fragments from a URL."""
    parsed = urlparse(url)
    cleaned = parsed._replace(query="", fragment="").geturl()
    return cleaned

def is_internal_url(url: str, base_url: str) -> bool:
    """Check whether a URL is internal to the given base."""
    try:
        return urlparse(url).netloc == urlparse(base_url).netloc
    except:
        return False
