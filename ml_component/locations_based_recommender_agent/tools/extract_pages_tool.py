# tools/extract_pages_tool.py
from langchain_openai import ChatOpenAI
from ml_component.locations_based_recommender_agent.web_utils.web_utils import (
    fetch_html,
    extract_links_from_html,
)
from ml_component.globals import api_key


class ExtractPagesTool:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)

    def run(self, input_str: str) -> str:
        """
        Given a string in the format 'product|||store_url', fetch internal links from the store website.
        Uses LLM reasoning to select the 3–5 most relevant URLs for product availability checking.
        """
        try:
            product, store_url = input_str.split("|||")
        except ValueError:
            return "[ERROR] Input must be in the format: 'product|||store_url'"

        html = fetch_html(store_url)
        if not html:
            return "[ERROR] Failed to fetch HTML content."

        all_links = extract_links_from_html(html, base_url=store_url)
        unique_links = list(set(all_links))

        if not unique_links:
            return "[ERROR] No internal links found on the page."

        sample_links = unique_links[:100]
        prompt = (
            f"The product to search for is: '{product}'.\n"
            f"Below is a list of internal URLs from the store website '{store_url}':\n\n"
            + "\n".join(sample_links)
            + "\n\nSelect the 3–5 links that are most likely to help determine if this product is sold in the store. "
              "Prefer links that contain product listings, catalog pages, or specific product names. "
              "Reply with one URL per line, no explanations."
        )

        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            return f"[ERROR] LLM failed: {e}"
