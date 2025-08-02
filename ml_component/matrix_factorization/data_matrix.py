import pandas as pd
import random

csv_file = "/ml_component/data/product_store_interactions.csv"
df = pd.read_csv(csv_file)


def set_pos_interaction(store_id, product_id):
    """
    Set the interaction to 1 (positive) for a specific store and product.
    """
    # Update the interaction to 1 for the given store_id and product_id
    df.loc[
        (df["store_id"] == store_id) & (df["product_id"] == product_id), "interaction"
    ] = 1

    # Save the updated DataFrame back to CSV
    df.to_csv(csv_file, index=False)
    print(f"Set positive interaction for Store {store_id} and Product {product_id}")


def set_neg_interaction(store_id, product_id):
    """
    Set the interaction to 0 (negative) for a specific store and product.
    """
    # Update the interaction to 0 for the given store_id and product_id
    df.loc[
        (df["store_id"] == store_id) & (df["product_id"] == product_id), "interaction"
    ] = 0

    # Save the updated DataFrame back to CSV
    df.to_csv(csv_file, index=False)
    print(f"Set negative interaction for Store {store_id} and Product {product_id}")
