import pytest
from fastapi.testclient import TestClient
from ml_component.api.model_fastapi_server import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def init_list_recommender():
    # Initialize ListBasedRecommender with default params
    response = client.post("/set_list_recommender")
    assert response.status_code == 200


def test_predict_categories_shape():
    response = client.get(
        "/predict_categories", params={"product_name": "Milk", "top_k": 3}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("product_name") == "Milk"
    cats = data.get("predicted_categories")
    assert isinstance(cats, list)
    assert len(cats) == 3


@pytest.mark.parametrize("top_k", [1, 5])
def test_recommend_similar_products(top_k):
    response = client.get(
        "/recommend_similar_products", params={"product_name": "iphone", "top_k": top_k}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("product_name") == "iphone"
    results = data.get("similar_products")
    assert isinstance(results, list)
    assert len(results) <= top_k
    print(len(results))


def test_recommend_by_list_name():
    # For a synthetic list name, check we receive a list
    response = client.get("/recommend_by_list_name", params={"list_name": "Groceries"})
    assert response.status_code == 200, response.text
    data = response.json()
    recs = data.get("recommended_products")
    assert isinstance(recs, list)
    # Should not include duplicates
    assert len(recs) == len(set(recs))
    print(len(recs))
