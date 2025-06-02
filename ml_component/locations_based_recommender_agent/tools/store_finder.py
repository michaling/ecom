from duckduckgo_search import DDGS
from urllib.parse import urlparse

class StoreWebsiteTool:
    def run(self, store_name: str) -> str:
        query = f"{store_name} official site"
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=5)
            for r in results:
                url = r.get("href", "")
                if url and store_name.lower() in urlparse(url).netloc.lower():
                    return url
        return ""
