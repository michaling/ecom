from typing import List
from langchain_openai import ChatOpenAI
from ml_component.globals import api_key
from ml_component.locations_based_recommender_agent.web_utils.web_utils import (
    fetch_html,
    extract_links_from_html,
    clean_url,
)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)


class ExtractRelevantStorePages:
    def run(self, input_str: str) -> str:
        product, store_url = input_str.split("|||")
        html = fetch_html(store_url)
        if not html:
            return ""

        all_links = extract_links_from_html(html, base_url=store_url)
        if not all_links:
            return ""

        # Normalize, clean, and deduplicate
        cleaned_links = list({clean_url(link) for link in all_links})

        # Keyword-based filtering
        keywords = ["products", "shop", "search", "catalog", "store", "stock", product.lower()]
        filtered_links = [
            link for link in cleaned_links
            if any(keyword in link.lower() for keyword in keywords)
        ]
        #TODO: enhance it for example with kravitz
        candidates = filtered_links[:15] if filtered_links else cleaned_links[:30]

        # Ask LLM to filter most relevant
        prompt = (
            f"You are helping check if the product '{product}' is available on the store website '{store_url}'.\n\n"
            f"Below are some internal links found on the site:\n" +
            "\n".join(candidates) +
            "\n\nPick the 3–5 links most likely to contain information about the product or catalog, stock, product listing, or search content.\n"
            "Return only those URLs, one per line."
        )

        result = llm.invoke(prompt).content.strip()
        return result


if __name__ == "__main__":
    tool = ExtractRelevantStorePages()
    product = "iPhone"
    store_url = "https://www.idigital.co.il/"
    input_str = f"{product}|||{store_url}"
    print("[DEBUG] Running ExtractRelevantStorePages on:")
    print("Product:", product)
    print("Store URL:", store_url)
    print("\n--- Relevant URLs ---")
    result = tool.run(input_str)
    print(result)