import os
import re
from langchain.utilities import SerpAPIWrapper

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"
os.environ["SERPAPI_API_KEY"] = "88e003fb4af697ba823079927159899e1a873185237534403e62fdfe072f49d3"

# Initialize SerpAPI wrapper
search = SerpAPIWrapper()

def get_store_website(store_name: str) -> str:
    """
    Searches the web for the store's official website.
    """
    query = f"{store_name} official site"
    results = search.run(query)
    urls = re.findall(r"https?://[^\s)>\"]+", results)
    for url in urls:
        if store_name.lower() in url.lower():
            return url.strip(".,\")'")
    return ""

def is_product_on_website(product_name: str, store_url: str) -> bool:
    """
    Searches within the store's domain for the product.
    """
    domain = store_url.split("//")[-1].split("/")[0]
    query = f"site:{domain} {product_name}"
    results = search.run(query)
    keywords = [product_name.lower(), "buy", "price", "add to cart", "in stock", "available"]
    return any(keyword in results.lower() for keyword in keywords)

def check_product_availability(product_name: str, store_name: str) -> bool:
    print(f"🔍 Looking for website of: {store_name}")
    store_url = get_store_website(store_name)
    if not store_url:
        print("❌ Could not find store website.")
        return False
    print(f"🌐 Found website: {store_url}")

    print(f"🔍 Searching for '{product_name}' on {store_name}'s site...")
    available = is_product_on_website(product_name, store_url)
    if available:
        print("✅ Product appears to be available.")
    else:
        print("❌ Product not found.")
    return available

# Example usage
if __name__ == "__main__":
    product = "Nutella"
    store = "Walmart"
    available = check_product_availability(product, store)
    print(f"\nFinal result: {available}")