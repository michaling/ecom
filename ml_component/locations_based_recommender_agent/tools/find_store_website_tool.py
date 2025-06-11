# tools/find_store_website_tool.py
from langchain_openai import ChatOpenAI
from ml_component.globals import api_key
import re


class FindStoreWebsiteTool:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)

    import re

    def run(self, store_name: str) -> str:
        prompt = (
            f"What is the official website of the store '{store_name}'? "
            "Reply only with the URL."
        )
        result = self.llm.invoke(prompt).content.strip()
        print(f"[DEBUG] LLM raw result: {result}")

        # Try to extract the URL using regex
        match = re.search(r"(https?://)?(www\.[\w\-\.]+\.\w+)", result)
        if match:
            # Add protocol if missing
            url = match.group(0)
            if not url.startswith("http"):
                url = "https://" + url
            return url
        return ""
