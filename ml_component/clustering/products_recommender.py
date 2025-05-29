import numpy as np
import pandas as pd
import joblib
from ml_component.clustering.embedding_search_engine import EmbeddingSearchEngine
from ml_component.globals import *
import os


class ProductRecommender:
    def __init__(self,
                 embedding_model_name: str = "all-mpnet-base-v2",
                 cache_dir: str = "cache"):
        """
        Initializes the product recommender using Supabase, classifier, and embedding model.
        """
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        # Load product data from Supabase
        self.products_df = self._load_products_from_supabase()

        # Validate columns
        required_cols = {"product_name", "category_name", "category_id"}
        if not required_cols.issubset(self.products_df.columns):
            raise ValueError(f"Supabase table must contain: {required_cols}")

        # Load neural network classifier using absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        classifier_path = os.path.join(base_dir, "clustering", "saved_models", "product_category_classifier_nn.joblib")
        self.classifier = joblib.load(classifier_path)
        self.categories = self.classifier.classes_

        # Build global embedding index
        self.embedding_engine = EmbeddingSearchEngine(model_name=embedding_model_name)
        self.embedding_engine.build_index(self.products_df["product_name"].tolist())

    def _load_products_from_supabase(self) -> pd.DataFrame:
        """
        Loads product data from Supabase table 'model_products'.
        """
        response = supabase.table("model_products").select("*").execute()
        data = response.data
        return pd.DataFrame(data)

    def predict_top_categories(self, input_product: str, top_k: int = 2):
        """
        Predicts the top_k most likely categories for a given product name.
        """
        probas = self.classifier.predict_proba([input_product])[0]
        top_indices = np.argsort(probas)[::-1][:top_k]
        return [self.categories[idx] for idx in top_indices]

    def find_similar_products(self, input_product: str, top_k: int = 5):
        """
        Finds top_k similar products to the given product name, filtered by predicted categories.
        """
        predicted_categories = set(self.predict_top_categories(input_product, top_k=2))

        candidates = self.embedding_engine.find_top_k(input_product, k=top_k * 5)

        # Filter and deduplicate
        filtered = []
        seen = set()
        for product in candidates:
            if product in seen:
                continue
            seen.add(product)

            row = self.products_df[self.products_df["product_name"] == product]
            if not row.empty and row.iloc[0]["category_name"] in predicted_categories:
                filtered.append(product)
            if len(filtered) == top_k:
                break

        return filtered
