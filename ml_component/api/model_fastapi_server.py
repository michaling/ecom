from fastapi import FastAPI, HTTPException
from ml_component.clustering.products_recommender import ProductRecommender
from ml_component.clustering.list_based_recommender import ListBasedRecommender

app = FastAPI()

# Global instances
product_recommender = ProductRecommender()
list_recommender = ListBasedRecommender()

"""
To set up the server run: ml_component.api.model_fastapi_server:app --reload
You need to be pwd on the same hierarchy as ml_component 
"""
@app.post("/set_list_recommender")
def set_list_recommender(k: int = 2, top_k_per_product: int = 1, final_m: int = 10):
    """
    Initializes the ListBasedRecommender with optional parameters.
    """
    global list_recommender
    list_recommender = ListBasedRecommender(
        k=k,
        top_k_per_product=top_k_per_product,
        final_m=final_m
    )
    return {"status": "ListBasedRecommender initialized"}


@app.get("/predict_categories")
def predict_categories(product_name: str, top_k: int = 2):
    if product_recommender is None:
        raise HTTPException(status_code=400, detail="ProductRecommender not initialized")
    return {
        "product_name": product_name,
        "predicted_categories": product_recommender.predict_top_categories(product_name, top_k)
    }


@app.get("/recommend_similar_products")
def recommend_similar_products(product_name: str, top_k: int = 5):
    if product_recommender is None:
        raise HTTPException(status_code=400, detail="ProductRecommender not initialized")
    return {
        "product_name": product_name,
        "similar_products": product_recommender.find_similar_products(product_name, top_k)
    }


@app.get("/recommend_by_list_name")
def recommend_by_list_name(list_name: str):
    if list_recommender is None:
        raise HTTPException(status_code=400, detail="ListBasedRecommender not initialized")
    return {
        "list_name": list_name,
        "recommended_products": list_recommender.recommend_from_list_name(list_name)
    }


@app.get("/recommend_top_lists")
def recommend_top_lists(list_name: str):
    if list_recommender is None:
        raise HTTPException(status_code=400, detail="ListBasedRecommender not initialized")
    return {
        "list_name": list_name,
        "similar_lists": list_recommender.get_similar_lists_by_name(list_name)
    }
