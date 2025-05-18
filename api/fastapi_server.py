
from fastapi import FastAPI
from pydantic import BaseModel

from clustering.products_recommender import ProductRecommender

app = FastAPI()

# Initialize once at startup
recommender = ProductRecommender(
    product_file="data/products.csv",
    classifier_file="clustering/saved_models/product_category_classifier.joblib"
)

class ProductRequest(BaseModel):
    product_name: str

@app.post("/recommend-products")
def recommend_products(req: ProductRequest):
    recommendations = recommender.find_similar_products(req.product_name, top_k=5)
    return {"recommendations": recommendations}

@app.post("/predict-categories")
def predict_categories(req: ProductRequest):
    predicted_categories = recommender.predict_top_categories(req.product_name, top_k=2)
    return {"predicted_categories": predicted_categories}
