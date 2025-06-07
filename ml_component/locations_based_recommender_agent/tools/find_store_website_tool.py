# find_store_website_tool.py
from langchain_openai import ChatOpenAI
from ml_component.globals import api_key

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)


class FindStoreWebsiteTool:
    def run(self, store_name: str) -> str:
        prompt = (f"What is the official website of the store '{store_name}'? Reply only with one URL that you are "
                  f"most confident about")
        result = llm.invoke(prompt).content.strip()
        return result if result.startswith("http") else ""


if __name__ == "__main__":
    tool = FindStoreWebsiteTool()
    print(tool.run("iDigital"))
