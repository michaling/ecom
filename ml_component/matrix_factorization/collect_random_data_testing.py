import supabase
import pandas as pd
import random
from ml_component.globals import *

# Load the existing CSV with store-product interactions
df = pd.read_csv("/ml_component/data/product_store_interactions.csv")

# Parameters
interaction_probability = 0.4


# Function to randomly set interactions
def set_random_interactions(row):
    # Randomly set interaction to 1 or 0 based on the interaction_probability
    return 1 if random.random() < interaction_probability else 0


def create_test_matrix():
    # Apply the function to set interactions
    df["interaction"] = df.apply(set_random_interactions, axis=1)
    # Save the updated DataFrame to a new CSV file
    df.to_csv("updated_product_store_interactions.csv", index=False)
    print(
        f"Generated random interactions and saved to 'updated_product_store_interactions.csv'"
    )


# Fetch store and product names from Supabase (only for statistics)
def fetch_store_and_product_names():
    stores_response = supabase.table("stores").select("store_id", "name").execute()
    products_response = (
        supabase.table("products").select("product_id", "name").execute()
    )

    # Store the data in dictionaries for easy lookup
    store_names = {store["store_id"]: store["name"] for store in stores_response.data}
    product_names = {
        product["product_id"]: product["name"] for product in products_response.data
    }

    return store_names, product_names


# Function to collect statistics
def collect_statistics(csv_file):
    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # Fetch store and product names (this will not alter your data)
    store_names, product_names = fetch_store_and_product_names()

    # Basic Statistics
    total_interactions = len(df)
    positive_interactions = len(df[df["interaction"] == 1])
    negative_interactions = total_interactions - positive_interactions
    positive_percentage = (positive_interactions / total_interactions) * 100

    # Get the number of unique stores and products
    num_stores = df["store_id"].nunique()
    num_products = df["product_id"].nunique()

    # Count of interactions by store
    interactions_by_store = df.groupby("store_id")["interaction"].sum()

    # Count of interactions by product
    interactions_by_product = df.groupby("product_id")["interaction"].sum()

    # Store with the most positive interactions
    store_with_most_interactions = interactions_by_store.idxmax()
    most_interactions_store = interactions_by_store.max()

    # Product with the most positive interactions
    product_with_most_interactions = interactions_by_product.idxmax()
    most_interactions_product = interactions_by_product.max()

    # Convert store and product IDs to names
    store_with_most_interactions_name = store_names.get(
        store_with_most_interactions, "Unknown Store"
    )
    product_with_most_interactions_name = product_names.get(
        product_with_most_interactions, "Unknown Product"
    )

    # Print out the statistics
    print(f"Total interactions: {total_interactions}")
    print(
        f"Positive interactions: {positive_interactions} ({positive_percentage:.2f}%)"
    )
    print(f"Negative interactions: {negative_interactions}")
    print(f"Number of stores: {num_stores}")
    print(f"Number of products: {num_products}")

    # Print top stores (with names)
    print("\nTop 5 stores with the most positive interactions:")
    top_stores = interactions_by_store.sort_values(ascending=False).head(5)
    for store_id, count in top_stores.items():
        store_name = store_names.get(store_id, "Unknown Store")
        print(f"Store: {store_name}, Interactions: {count}")

    # Print top products (with names)
    print("\nTop 5 products with the most positive interactions:")
    top_products = interactions_by_product.sort_values(ascending=False).head(5)
    for product_id, count in top_products.items():
        product_name = product_names.get(product_id, "Unknown Product")
        print(f"Product: {product_name}, Interactions: {count}")

    # Print store with most positive interactions
    print(
        f"\nStore with most positive interactions: Store {store_with_most_interactions_name} ({most_interactions_store} interactions)"
    )

    # Print product with most positive interactions
    print(
        f"Product with most positive interactions: Product {product_with_most_interactions_name} ({most_interactions_product} interactions)"
    )

    # Matrix Sparsity
    sparsity = 1 - (positive_interactions / total_interactions)
    print(
        f"\nMatrix Sparsity: {sparsity:.4f} (i.e., {positive_percentage:.2f}% of the matrix is populated with positive interactions)"
    )


create_test_matrix()
# Example usage (make sure the CSV file exists with the expected format)
collect_statistics("updated_product_store_interactions.csv")
