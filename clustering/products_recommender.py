import os
import numpy as np
import pandas as pd
import joblib
from sentence_transformers import SentenceTransformer
import faiss

import os
import numpy as np
import pandas as pd
import joblib
from sentence_transformers import SentenceTransformer
import faiss

class ProductRecommender:
    def __init__(self, product_file: str, classifier_file: str, embedding_model_name: str = "all-mpnet-base-v2", cache_dir="cache"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.product_file = os.path.join(base_dir, product_file)
        self.classifier_file = os.path.join(base_dir, classifier_file)
        self.embedding_model_name = embedding_model_name
        self.cache_dir = os.path.join(base_dir, cache_dir)


        # Load sentence transformer model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        # Load products dataframe
        self.products_df = pd.read_csv(self.product_file)

        if "product_name" not in self.products_df.columns or "category" not in self.products_df.columns:
            raise ValueError("CSV must contain 'product_name' and 'category' columns")

        # Load or compute embeddings
        self.embeddings = self._load_or_compute_embeddings()

        # Build global FAISS index (we still need it for partial searches)
        self.index = self._build_faiss_index()

        # Load the category classifier
        self.classifier = joblib.load(self.classifier_file)
        self.categories = self.classifier.classes_

    def _load_or_compute_embeddings(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        embeddings_path = os.path.join(self.cache_dir, "product_embeddings.npy")

        if os.path.exists(embeddings_path):
            print("Loading cached embeddings...")
            embeddings = np.load(embeddings_path)
        else:
            print("Computing embeddings...")
            embeddings = self.embedding_model.encode(self.products_df['product_name'].tolist(), show_progress_bar=True, convert_to_numpy=True)
            np.save(embeddings_path, embeddings)
        return embeddings

    def _build_faiss_index(self):
        dim = self.embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(self.embeddings)
        return index

    def predict_top_categories(self, input_product: str, top_k: int = 2):
        """Predict top_k categories for a given input product name."""
        probas = self.classifier.predict_proba([input_product])[0]
        top_indices = np.argsort(probas)[::-1][:top_k]
        return [self.categories[idx] for idx in top_indices]

    def find_similar_products(self, input_product: str, top_k: int = 5):
        """Find top_k most similar products within the top predicted categories."""
        # Step 1: Predict top-2 categories
        predicted_categories = self.predict_top_categories(input_product, top_k=2)

        # Debug print
        print(f"\n[DEBUG] Predicted categories: {predicted_categories}")

        # Step 2: Filter products for ONLY those categories (fresh every time!)
        mask = self.products_df['category'].isin(predicted_categories)
        filtered_products = self.products_df[mask].reset_index(drop=True)

        if filtered_products.empty:
            print("[DEBUG] No products found in predicted categories. Returning empty list.")
            return []

        # Step 3: Recompute filtered embeddings (fresh every time!)
        filtered_embeddings = self.embedding_model.encode(
            filtered_products['product_name'].tolist(),
            convert_to_numpy=True
        )
        filtered_embeddings = np.asarray(filtered_embeddings, dtype=np.float32)

        # Step 4: Build a temporary FAISS index for just this query
        dim = filtered_embeddings.shape[1]
        temp_index = faiss.IndexFlatL2(dim)
        temp_index.add(filtered_embeddings)

        # Step 5: Embed the input product
        input_vec = self.embedding_model.encode([input_product], convert_to_numpy=True)
        input_vec = np.asarray(input_vec, dtype=np.float32)

        # Step 6: Search inside the filtered products
        distances, indices = temp_index.search(input_vec, top_k)

        # Step 7: Collect recommended product names
        recommended_products = [filtered_products.iloc[idx]['product_name'] for idx in indices[0]]
        return recommended_products

