from ml_component.locations_based_recommender_agent.web_utils.web_utils import fetch_html, extract_text_from_html
from langchain_openai import ChatOpenAI
from ml_component.globals import api_key

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)


class SummarizeStorePageForProduct:
    def run(self, input_str: str) -> str:
        """
        Input: "<product>|||<url>"
        Output: "True (confidence: 0.9)" or "False (confidence: 0.2)"
        """
        try:
            product, url = input_str.split("|||")
        except ValueError:
            return "[ERROR] Input must be in the format '<product>|||<url>'"

        html = fetch_html(url)
        if not html:
            return "False (confidence: 0.0)"

        text = extract_text_from_html(html)[:3000]

        prompt = (
            f"You are a smart AI assistant helping to determine whether a product is likely sold in a store based on part of its website content.\n\n"
            f"Store page URL: {url}\n"
            f"Truncated page content:\n{text}\n\n"
            f"Product to check: '{product}'\n\n"
            f"Please do the following:\n"
            f"1. Check if the product name appears in the text, even with minor spelling mistakes.\n"
            f"2. Be forgiving if the exact model (e.g., 'iPhone 16') is not present — general model families (e.g., 'iPhone') are acceptable.\n"
            f"3. Also consider synonyms, brand mentions, and category matches (e.g., 'smartphones', 'Apple products', 'skincare').\n"
            f"4. Your decision can be based on the likelihood that this type of product would be sold given the context.\n\n"
            f"Reply in JSON format with the following keys:\n"
            f"- 'answer': True or False\n"
            f"- 'confidence': float between 0 and 1\n"
            f"- 'reason': short sentence explaining your reasoning\n\n"
            f"Only output valid JSON. Be tolerant of naming or model variations."
        )

        result = llm.invoke(prompt).content.strip()
        return result


if __name__ == "__main__":
    tool = SummarizeStorePageForProduct()
    # Example product and one of the URLs returned by ExtractRelevantStorePagesTool
    product = "android"
    url = "https://www.idigital.co.il/iphone/iphone16_content/"

    input_str = f"{product}|||{url}"
    result = tool.run(input_str)
    print(result)