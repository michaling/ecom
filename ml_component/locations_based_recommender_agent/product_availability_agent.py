from langgraph.graph import END, StateGraph
from typing import TypedDict, List, Optional, Dict, Tuple
from langchain_core.runnables import Runnable
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from ml_component.locations_based_recommender_agent.tools.find_store_website_tool import FindStoreWebsiteTool
from ml_component.locations_based_recommender_agent.tools.extract_pages_tool import ExtractPagesTool
from ml_component.locations_based_recommender_agent.tools.summarize_page_tool import SummarizeStorePageTool


# === Agent State ===
class AgentState(TypedDict):
    product: str
    store: str
    store_url: str
    page_urls: List[str]
    current_index: int
    answer: str
    price: Optional[str]


# === FAISS-backed result cache ===
class ResultCache:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(384)
        self.entries: Dict[str, Tuple[str, str]] = {}  # index → (store, product)
        self.results: Dict[str, Dict] = {}  # "store|product" → result

    def _id(self, store: str, product: str) -> str:
        return f"{store.strip().lower()}|{product.strip().lower()}"

    def add(self, store: str, product: str, result: Dict):
        key = self._id(store, product)
        if key in self.results:
            return
        embedding = self.model.encode(key, normalize_embeddings=True).astype(np.float32).reshape(1, -1)
        self.index.add(embedding)
        self.entries[str(len(self.entries))] = (store, product)
        self.results[key] = result
        print(f"[FAISS]  Cached result for: {key}")

    def retrieve_similar(self, store: str, product: str, threshold: float = 0.85) -> Optional[Dict]:
        key = self._id(store, product)
        if len(self.entries) == 0:
            return None
        embedding = self.model.encode(key, normalize_embeddings=True).astype(np.float32).reshape(1, -1)
        D, I = self.index.search(embedding, k=1)
        if D[0][0] < (2 - 2 * threshold):  # cosine distance threshold
            match_store, match_product = self.entries[str(I[0][0])]
            match_key = self._id(match_store, match_product)
            print(f"[FAISS]  Reused from similar: {match_key} (dist={D[0][0]:.4f})")
            return self.results.get(match_key)
        return None


# === Main Agent ===
class ProductAvailabilityAgent:
    def __init__(self):
        self.find_site_tool = FindStoreWebsiteTool()
        self.extract_pages_tool = ExtractPagesTool()
        self.summarizer_tool = SummarizeStorePageTool()
        self.graph = self._build_graph()
        self.cache = ResultCache()

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
        print(f"[Node]  Summarizing page {index + 1}/{len(urls)}: {current_url}")
        result_str = self.summarizer_tool.run(input_str)

        try:
            result = json.loads(result_str)
            confidence = float(result.get("confidence", 0))
            print(f"[Node]  LLM Response → confidence={confidence} | answer={result.get('answer')}")

            if result.get("answer") is True and confidence > 0.7:
                price = result.get("price", None)
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
        cached = self.cache.retrieve_similar(store, product)
        if cached:
            return cached

        # Run full graph
        result = self.graph.invoke({
            "product": product,
            "store": store
        })

        # Parse and save result
        try:
            parsed = json.loads(result["answer"])
        except Exception:
            parsed = {
                "answer": False,
                "confidence": 0.0,
                "reason": result["answer"].strip() if result.get("answer", "").strip() else "UNKNOWN",
                "price": None
            }

        self.cache.add(store, product, parsed)
        return parsed


# === Manual Run Example ===
if __name__ == "__main__":
    agent = ProductAvailabilityAgent()
    res = agent.check_product("pillow", "superpharm")
    print(json.dumps(res, indent=2))
