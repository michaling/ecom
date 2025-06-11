import pytest
from fastapi.testclient import TestClient
from httpx import Response
import respx

from app.main import app  # assuming your FastAPI app is defined here
from app.supabase_client import supabase

client = TestClient(app)

# Fixture to clear and set up a temporary supabase-like table
@pytest.fixture(autouse=True)
def clear_tables(monkeypatch):
    # Monkeypatch supabase table methods to use in-memory dicts
    data_store = {
        "lists": [],
        "lists_items": [],
        "items_suggestions": []
    }

    class FakeTable:
        def __init__(self, name):
            self.name = name
        def select(self, *args, **kwargs): return self
        def eq(self, key, value): return self
        def delete(self): return self
        def insert(self, payload):
            data_store[self.name].extend(payload if isinstance(payload, list) else [payload])
            class Dummy:
                data = data_store[self.name]
                def execute(self): return self
            return Dummy()
        def single(self): return self
        def execute(self):
            class Dummy:
                data = data_store.get(self.name)
            return Dummy()
    monkeypatch.setattr(supabase, 'table', lambda name: FakeTable(name))
    yield

@respx.mock
def test_create_list_and_recommendations():
    # Mock ML API response
    ml_url = "http://localhost:8000/recommend_by_list_name"
    respx.get(ml_url).mock(return_value=Response(200, json={
        "list_name": "Groceries",
        "recommended_products": ["Milk", "Eggs", "Bread"]
    }))

    # Create list payload
    payload = {
        "name": "Groceries",
        "items": [
            {"name": "Milk", "is_checked": False, "geo_alert": None, "deadline": None}
        ],
        "geo_alert": False,
        "deadline": None
    }
    response = client.post("/lists?user_id=test_user", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["list_id"] is not None

    # After creation, items_suggestions should exclude "Milk"
    suggestions = supabase.table("items_suggestions").select().execute().data
    suggested_names = {s["suggestion_text"] for s in suggestions}
    assert "Eggs" in suggested_names
    assert "Bread" in suggested_names
    assert "Milk" not in suggested_names

@respx.mock
def test_refresh_all_recommendations():
    # Setup existing list entries
    supabase.table("lists").insert({"list_id": 1, "name": "Party"}).execute()
    supabase.table("lists_items").insert([
        {"list_id": 1, "name": "Chips"},
        {"list_id": 1, "name": "Soda"}
    ]).execute()

    # Mock ML response for existing list
    ml_url = "http://localhost:8000/recommend_by_list_name"
    respx.get(ml_url).mock(return_value=Response(200, json={
        "list_name": "Party",
        "recommended_products": ["Chips", "Cake", "Soda"]
    }))

    # Call refresh job directly
    from app.lists import lists
    import asyncio
    asyncio.run(lists.fetch_and_update_recommendations())

    # Check suggestions: should only have "Cake"
    suggestions = supabase.table("items_suggestions").select().execute().data
    suggested_names = {s["suggestion_text"] for s in suggestions}
    assert suggested_names == {"Cake"}
