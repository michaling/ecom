import pandas as pd
import random
from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split
from surprise import accuracy
import supabase
from ml_component.globals import *

# Fetch store and product names from Supabase
def fetch_store_and_product_names():
    stores_response = supabase.table("stores").select("store_id", "name").execute()
    products_response = supabase.table("products").select("product_id", "name").execute()

    # Store the data in dictionaries for easy lookup
    store_names = {store["store_id"]: store["name"] for store in stores_response.data}
    product_names = {product["product_id"]: product["name"] for product in products_response.data}

    return store_names, product_names


# Load the product-store interaction data
df = pd.read_csv(
    "/ml_component/matrix_factorization/updated_product_store_interactions.csv")

# Map UUIDs to integers for product_id and store_id
product_id_mapping = {product_id: idx for idx, product_id in enumerate(df['product_id'].unique())}
store_id_mapping = {store_id: idx for idx, store_id in enumerate(df['store_id'].unique())}

# Apply the mapping to convert UUIDs to integers
df['product_id'] = df['product_id'].map(product_id_mapping)
df['store_id'] = df['store_id'].map(store_id_mapping)

# Define the format of the data
reader = Reader(rating_scale=(0, 1))  # Rating scale between 0 and 1 (for product availability)

# Load data into Surprise format
data = Dataset.load_from_df(df[['product_id', 'store_id', 'interaction']], reader)

# Split data into training and testing sets
trainset, testset = train_test_split(data, test_size=0.2)

# Initialize the SVD algorithm for matrix factorization
svd = SVD()

# Train the model
svd.fit(trainset)

# Test the model
predictions = svd.test(testset)

# Evaluate accuracy using RMSE
rmse = accuracy.rmse(predictions)

# Randomly pick a store_id and product_id from the list
random_store_id_int = random.choice(df['store_id'].unique())  # Random store ID from the dataset
random_product_id_int = random.choice(df['product_id'].unique())  # Random product ID from the dataset

# Map integer store_id and product_id back to UUIDs
store_names, product_names = fetch_store_and_product_names()

# Convert the randomly selected integer IDs back to UUIDs
random_store_id_uuid = list(store_id_mapping.keys())[list(store_id_mapping.values()).index(random_store_id_int)]
random_product_id_uuid = list(product_id_mapping.keys())[list(product_id_mapping.values()).index(random_product_id_int)]

# Fetch the store and product names from Supabase using UUIDs
store_name = store_names.get(random_store_id_uuid, "Unknown Store")
product_name = product_names.get(random_product_id_uuid, "Unknown Product")

# Predict the availability of the randomly selected product in the randomly selected store
pred = svd.predict(random_product_id_int, random_store_id_int)

# Apply a threshold to classify the prediction as 0 or 1
#predicted_interaction = 1 if pred.est >= 0.5 else 0

print(
    f"Predicted interaction for Product {product_name} (ID: {random_product_id_uuid}) in Store {store_name} (ID: {random_store_id_uuid}): {pred.est}")
