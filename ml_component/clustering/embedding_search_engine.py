import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingSearchEngine:
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name)
        self.index_items: List[str] = []
        self.embeddings: np.ndarray = None

    def build_index(self, items: List[str]):
        self.index_items = items
        self.embeddings = self.model.encode(items, convert_to_numpy=True)

    def encode_single(self, item: str) -> np.ndarray:
        return self.model.encode([item], convert_to_numpy=True)

    def find_top_k(self, query: str, k: int = 5) -> List[str]:
        if not self.index_items or self.embeddings is None:
            raise ValueError("Index not built. Call build_index() first.")
        query_vec = self.encode_single(query)
        scores = cosine_similarity(query_vec, self.embeddings)[0]
        top_k_idx = np.argsort(scores)[::-1][:k]
        return [self.index_items[i] for i in top_k_idx]
