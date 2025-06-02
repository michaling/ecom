import os
from urllib.parse import urlparse
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from product_tools import find_store_website, product_appears_on_site
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize language model
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=api_key)

# Tool: find the store's website
def find_website(store: str) -> str:
    print(f"[DEBUG] Searching for website of: {store}")
    return find_store_website(store)

# Tool: check if a product appears on the given store site
def check_product(product_input: str) -> bool:
    try:
        product_name, store_url = product_input.split("|||")
        parsed = urlparse(store_url)
        domain = parsed.netloc
        print(f"[DEBUG] Checking '{product_name}' on domain: {domain}")
        return product_appears_on_site(product_name, domain)
    except Exception as e:
        print(f"[ERROR] Parsing input for check_product: {e}")
        return False

# Register tools
tools = [
    Tool(name="FindStoreWebsite", func=find_website, description="Find website for a given store"),
    Tool(name="CheckProductOnSite", func=check_product, description="Check if a product exists on a given store website (input: '<product>|||<store_url>')")
]

# Build agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Example query
product = "iphone"
store = "idigital"
question = f"Is the product '{product}' available at {store}? First find the store's website, then check if the product appears on the site. Answer only True or False."

# Execute using invoke instead of deprecated run()
response = agent.invoke({"input": question})
print("Agent Final Answer:", response["output"])