from langgraph.graph import END, StateGraph
from typing import TypedDict, List, Optional, Dict
from langchain_core.runnables import Runnable
import json

from ml_component.locations_based_recommender_agent.tools.find_store_website_tool import FindStoreWebsiteTool
from ml_component.locations_based_recommender_agent.tools.extract_pages_tool import ExtractPagesTool
from ml_component.locations_based_recommender_agent.tools.summarize_page_tool import SummarizeStorePageTool


# === Define State ===
class AgentState(TypedDict):
    product: str
    store: str
    store_url: str
    page_urls: List[str]
    current_index: int
    answer: str
    price: Optional[str]


class ProductAvailabilityAgent:
    def __init__(self):
        self.find_site_tool = FindStoreWebsiteTool()
        self.extract_pages_tool = ExtractPagesTool()
        self.summarizer_tool = SummarizeStorePageTool()
        self.graph = self._build_graph()

    def _find_store_website_node(self, state: AgentState) -> AgentState:
        print(f"[Node] Finding website for store: {state['store']}")
        store_url = self.find_site_tool.run(state["store"])
        print(f"[Node] Found URL: {store_url}")
        return {
            "product": state["product"],
            "store": state["store"],
            "store_url": store_url,
            "page_urls": [],
            "current_index": 0,
            "answer": "",
            "price": None
        }

    def _extract_pages_node(self, state: AgentState) -> AgentState:
        print(f"[Node] Extracting internal links for: {state['store_url']}")
        input_str = f'{state["product"]}|||{state["store_url"]}'
        raw_links = self.extract_pages_tool.run(input_str)
        urls = [url.strip() for url in raw_links.splitlines() if url.strip()]
        print(f"[Node] Found top {len(urls)} links")

        return {
            **state,
            "page_urls": urls[:5],
            "current_index": 0,
            "answer": "",
            "price": None
        }

    def _summarize_page_node(self, state: AgentState) -> AgentState:
        index = state["current_index"]
        urls = state["page_urls"]

        if index >= len(urls):
            print("[Node] All pages checked, no high confidence found.")
            return {**state, "answer": "False (No high confidence found in any page)"}

        current_url = urls[index]
        input_str = f'{state["product"]}|||{current_url}'
        print(f"[Node] 📝 Summarizing page {index + 1}/{len(urls)}: {current_url}")
        result_str = self.summarizer_tool.run(input_str)

        try:
            result = json.loads(result_str)
            confidence = float(result.get("confidence", 0))
            print(f"[Node] 🤖 LLM Response → confidence={confidence} | answer={result.get('answer')}")

            if result.get("answer") is True and confidence > 0.7:
                price = result.get("price", None)
                if price:
                    print(f"[Node] Price Found: {price}")

                return {
                    **state,
                    "answer": json.dumps({
                        "answer": True,
                        "confidence": confidence,
                        "reason": result.get("reason", ""),
                        "price": price
                    }),
                    "price": price
                }

        except Exception as e:
            print(f"[Node] JSON parse failed: {e}")

        return {**state, "current_index": index + 1}

    def _continue_or_stop(self, state: AgentState) -> str:
        if state.get("answer"):
            return END
        if state["current_index"] >= len(state["page_urls"]):
            return END
        return "summarize_next"

    def _build_graph(self) -> Runnable:
        builder = StateGraph(AgentState)
        builder.add_node("find_site", self._find_store_website_node)
        builder.add_node("extract_pages", self._extract_pages_node)
        builder.add_node("summarize_next", self._summarize_page_node)
        builder.set_entry_point("find_site")
        builder.add_edge("find_site", "extract_pages")
        builder.add_edge("extract_pages", "summarize_next")
        builder.add_conditional_edges("summarize_next", self._continue_or_stop, {
            "summarize_next": "summarize_next",
            END: END
        })
        return builder.compile()

    def check_product(self, product: str, store: str) -> Dict:
        result = self.graph.invoke({
            "product": product,
            "store": store
        })

        # Parse result["answer"] if JSON
        try:
            return json.loads(result["answer"])
        except Exception:
            return {
                "answer": False,
                "confidence": 0.0,
                "reason": result.get("answer", "Unknown"),
                "price": None
            }


if __name__ == "__main__":
    agent = ProductAvailabilityAgent()
    response = agent.check_product("pillow", "superpharm")
    print(json.dumps(response, indent=2))
