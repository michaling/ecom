from typing import List
from collections import Counter
from ml_component.clustering.embedding_search_engine import EmbeddingSearchEngine
from ml_component.globals import *
from ml_component.clustering.products_recommender import ProductRecommender


class ListBasedRecommender:
    def __init__(
        self,
        embedding_model_name: str = "all-mpnet-base-v2",
        k: int = 2,
        top_k_per_product: int = 1,
        final_m: int = 10,
    ):
        """
        Initializes the list-based recommender.
        :param embedding_model_name: Embedding model to use for list name similarity
        :param k: Number of similar lists to retrieve
        :param top_k_per_product: Number of similar products per product
        :param final_m: Number of products to return in the final recommendation
        """
        self.supabase = supabase
        self.product_recommender = ProductRecommender()
        self.embedding_model_name = embedding_model_name
        self.k = k
        self.top_k_per_product = top_k_per_product
        self.final_m = final_m

        self.list_name_engine = EmbeddingSearchEngine(
            model_name=self.embedding_model_name
        )

    def _get_all_lists(self) -> List[dict]:
        response = self.supabase.table("lists").select("*").execute()
        return response.data if response.data else []

    def _get_list_items_names(self, list_id: str) -> List[str]:
        response = (
            self.supabase.table("lists_items")
            .select("name")
            .eq("list_id", list_id)
            .execute()
        )
        return (
            [item["name"] for item in response.data if "name" in item]
            if response.data
            else []
        )

    def get_similar_lists_by_name(self, input_list_name: str) -> List[dict]:
        """
        Returns the most similar lists to the input list name.
        """
        all_lists = self._get_all_lists()
        list_names = [lst["name"] for lst in all_lists if "name" in lst]

        if not list_names:
            print("[WARN] No lists found in Supabase.")
            return []

        self.list_name_engine.build_index(list_names)
        similar_names = self.list_name_engine.find_top_k(input_list_name, k=self.k)
        similar_lists = [lst for lst in all_lists if lst["name"] in similar_names]

        if not similar_lists:
            print(f"[WARN] No similar lists found for input: {input_list_name}")
            return []

        return similar_lists

    def recommend_from_list_name(self, list_name: str) -> List[str]:
        # Step 1: Get all lists and names
        similar_lists = self.get_similar_lists_by_name(list_name)
        if not similar_lists:
            return []

        # Step 2: Collect all product names (with duplicates preserved)
        all_product_names = []
        for lst in similar_lists:
            product_names = self._get_list_items_names(lst["list_id"])
            all_product_names.extend(product_names)

        # Step 3: Recommend similar products
        recommendation_counter = Counter()
        for product_name in all_product_names:
            if product_name:
                similar = self.product_recommender.find_similar_products(
                    product_name, top_k=self.top_k_per_product
                )
                recommendation_counter.update(similar)

        # Step 4: Return top-m most frequently recommended products
        return [
            product for product, _ in recommendation_counter.most_common(self.final_m)
        ]
