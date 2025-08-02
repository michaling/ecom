# tools/summarize_store_page_tool.py
from langchain_openai import ChatOpenAI
from ml_component.locations_based_recommender_agent.web_utils.web_utils import (
    fetch_html,
    extract_text_from_html,
)
from ml_component.globals import api_key
import tiktoken


class SummarizeStorePageTool:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

    def truncate_to_token_limit(self, text: str, limit: int = 3000) -> str:
        tokens = self.encoding.encode(text)
        if len(tokens) > limit:
            tokens = tokens[:limit]
        return self.encoding.decode(tokens)

    def run(self, input_str: str) -> str:
        try:
            product, url = input_str.split("|||")
        except ValueError:
            return '{"answer": false, "confidence": 0.0, "reason": "Invalid input format", "price": null}'

        html = fetch_html(url)
        if not html:
            return '{"answer": false, "confidence": 0.0, "reason": "Failed to fetch HTML", "price": null}'

        raw_text = extract_text_from_html(html)
        text = self.truncate_to_token_limit(raw_text)

        prompt = (
            f"You are a smart AI assistant helping to determine whether a product is likely sold in a store based on part of its website content.\n\n"
            f"Store page URL: {url}\n"
            f"Truncated page content:\n{text}\n\n"
            f"Product to check: '{product}'\n\n"
            f"Instructions:\n"
            f"1. Determine if the product is likely sold on this page (allow close matches like 'iPhone' instead of 'iPhone 16').\n"
            f"2. If the product is found with high confidence (above 0.7), try to extract the price if explicitly mentioned. If the price is not mentioned, return null for price.\n"
            f"3. Consider brand mentions, category matches, and product-related context.\n"
            f"4. Respond in the following strict JSON format:\n"
            f'{{"answer": true/false, "confidence": float, "reason": "...", "price": "$..." or null}}'
        )

        return self.llm.invoke(prompt).content.strip()
