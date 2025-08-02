from ml_component.globals import *
import pandas as pd


def get_stores():
    return supabase.table("stores").select("store_id", "name").execute()


def insert_products(product_names):
    for product_name in product_names:
        existing_product = (
            supabase.table("products")
            .select("product_id")
            .eq("name", product_name)
            .execute()
        )
        if existing_product.data:
            print(f"Product '{product_name}' already exists. Skipping insert.")
        else:
            supabase.table("products").insert({"name": product_name}).execute()


def create_data_matrix():
    # Fetch stores from Supabase
    stores_response = supabase.table("stores").select("store_id", "name").execute()
    stores_data = stores_response.data
    # Extract store data (store IDs)
    store_ids = [store["store_id"] for store in stores_data]
    # Initialize an empty list to hold product data
    all_products = []
    # Batch size for pagination
    batch_size = 1000  # You can adjust this value
    offset = 0
    # Fetch products in batches
    while True:
        products_response = (
            supabase.table("products")
            .select("product_id", "name")
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        # If no products are returned, break the loop
        if not products_response.data:
            break
        # Append the current batch of products to the list
        all_products.extend(products_response.data)
        # Update offset for the next batch
        offset += batch_size
    # Extract product data (product IDs)
    product_ids = [product["product_id"] for product in all_products]
    # Create a list of interactions (store_id, product_id)
    interactions = []
    for store_id in store_ids:
        for product_id in product_ids:
            interactions.append(
                {"product_id": product_id, "store_id": store_id, "interaction": 0}
            )
    # Create a DataFrame from the interactions list
    df = pd.DataFrame(interactions)
    # Save the DataFrame to CSV
    df.to_csv("product_store_interactions.csv", index=False)


create_data_matrix()
