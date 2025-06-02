from langchain.agents import Tool
from langchain_openai import ChatOpenAI
from tools.store_finder import StoreWebsiteTool
from tools.product_indicators import ProductSearchSignalTool, URLMatchSignalTool, StoreDescriptionSignalTool
from scoring.score_calculator import ScoreCombiner

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

store_tool = StoreWebsiteTool()
url_tool = URLMatchSignalTool()
search_tool = ProductSearchSignalTool()
desc_tool = StoreDescriptionSignalTool()
scorer = ScoreCombiner()

def smart_availability_checker(query: str):
    """Wrapper to run all indicators and return a score-based decision."""
    product, store = query.split("|||")

    print(f"[INFO] Finding store website for '{store}'...")
    store_url = store_tool.run(store)
    print(f"[INFO] Got store URL: {store_url}")

    if not store_url:
        return "Score: 0.0 → Product not available (no website found)."

    # Run indicator functions
    url_match = url_tool.run(f"{product}|||{store_url}")
    product_search = search_tool.run(f"{product}|||{store_url}")
    store_desc = desc_tool.run(f"{store}|||{product}")

    # Compute final score
    score = scorer.compute(url_match, product_search, store_desc)
    available = score >= 0.5
    return f"Score: {score} → Product {'available' if available else 'not available'}."

# Tools for LangChain (optional, currently unused)
tools = [
    Tool(name="FindStoreWebsite", func=store_tool.run, description="Find official website of a store"),
    Tool(name="URLMatchSignal", func=url_tool.run, description="Check if product name appears in a store URL"),
    Tool(name="ProductSearchSignal", func=search_tool.run, description="Search store site for product and use LLM to decide likelihood"),
    Tool(name="StoreDescriptionSignal", func=desc_tool.run, description="Analyze store description to determine if it might sell a product"),
]

# Sample run
if __name__ == "__main__":
    product = "Nutella"
    store = "Walmart"
    question = f"{product}|||{store}"
    print("→", smart_availability_checker(question))
