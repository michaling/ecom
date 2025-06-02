from ml_component.locations_based_recommender_agent.web_utils.web_utils import *
from ml_component.globals import api_key
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)


class URLMatchSignalTool:
    def run(self, query: str) -> bool:
        product, store_url = query.split("|||")
        return product.lower() in store_url.lower()


class ProductSearchSignalTool:
    def run(self, query: str) -> bool:
        product, store_url = query.split("|||")
        html = fetch_html(store_url)
        prompt = f"""Extracted site content:\n{html[:2000]}\n\nDoes it seem that '{product}' is available on this store? Reply only True or False."""
        return "true" in llm.invoke(prompt).content.lower()


class StoreDescriptionSignalTool:
    def run(self, store_name: str) -> bool:
        description = f"{store_name} is a pharmacy chain that sells cosmetics, baby care, and hygiene products."
        prompt = f"Based on the store description: '{description}', does the store likely sell the product '{store_name}'? Reply only True or False."
        return "true" in llm.invoke(prompt).content.lower()
