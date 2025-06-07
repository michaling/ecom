from langchain_openai import ChatOpenAI
import json
from ml_component.globals import api_key
from ml_component.locations_based_recommender_agent.tools.find_store_website_tool import FindStoreWebsiteTool
from ml_component.locations_based_recommender_agent.tools.extract_relevant_pages_tool import ExtractRelevantStorePages
from ml_component.locations_based_recommender_agent.tools.summerize_page_tool import SummarizeStorePageForProduct

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)

# Instantiate tools
find_site_tool = FindStoreWebsiteTool()
extract_pages_tool = ExtractRelevantStorePages()
summarizer_tool = SummarizeStorePageForProduct()

def check_product_availability(query: str) -> str:
    product, store = query.split("|||")

    # Step 1: Get store URL
    print(f"[STEP 1] Searching for official site of: {store}")
    store_url = find_site_tool.run(store)
    if not store_url:
        return "False (Store website not found)"

    # Step 2: Extract relevant page URLs
    print(f"[STEP 2] Extracting relevant pages from: {store_url}")
    pages_str = extract_pages_tool.run(f"{product}|||{store_url}")
    page_urls = [url.strip() for url in pages_str.splitlines() if url.strip()]

    if not page_urls:
        return "False (No relevant pages found)"

    # Step 3: Analyze pages
    print(f"[STEP 3] Scanning {len(page_urls)} relevant pages...")
    for url in page_urls:
        response = summarizer_tool.run(f"{product}|||{url}")
        try:
            parsed = json.loads(response) if isinstance(response, str) else response
            print(f"[PAGE CHECK] {url} → {parsed}")
            if parsed.get("answer") is True and float(parsed.get("confidence", 0)) > 0.7:
                return f"True (High confidence on: {url})"
        except Exception as e:
            print(f"[WARN] Failed to parse response for {url}: {e}")
            continue

    return "False (No page met confidence threshold)"


# Main
if __name__ == "__main__":
    product = "iphone"
    store = "idigital"
    input_str = f"{product}|||{store}"
    result = check_product_availability(input_str)
    print("➤ Final Decision:", result)
