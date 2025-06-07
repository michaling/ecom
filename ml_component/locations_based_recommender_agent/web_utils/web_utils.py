import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Optional
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def fetch_html(url: str) -> str:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        return driver.page_source
    finally:
        driver.quit()

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
