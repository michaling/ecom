from duckduckgo_search import DDGS
from urllib.parse import urlparse

def find_store_website(store_name: str) -> str:
    """Search DuckDuckGo for the official website of a store."""
    query = f"{store_name} official site"
    fallback = ""
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)
        for r in results:
            href = r.get("href")
            if not href:
                continue
            domain = urlparse(href).netloc
            if store_name.lower() in domain.lower():
                return href  # best match
            if not fallback:
                fallback = href  # store first valid fallback
    return fallback  # fallback if no strong match

def product_appears_on_site(product_name: str, store_domain: str, max_results: int = 5) -> bool:
    """Search DuckDuckGo for product presence on a store's domain."""
    query = f"{product_name} site:{store_domain}"
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)
        for r in results:
            if product_name.lower() in r["title"].lower() or product_name.lower() in r["body"].lower():
                print(f"[MATCH] {r['title']} - {r['href']}")
                return True
    return False
