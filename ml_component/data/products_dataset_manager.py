import pandas as pd


def add_empty_product_id_column(input_csv: str, output_csv: str):
    """
    Adds an empty 'product_id' column to the start of the CSV and saves the result.

    Args:
        input_csv (str): Path to the input CSV.
        output_csv (str): Path to write the modified CSV.
    """
    df = pd.read_csv(input_csv)

    # Insert empty 'product_id' column at position 0
    df.insert(0, "product_id", "")

    df.to_csv(output_csv, index=False)


# Example usage
add_empty_product_id_column(
    "products_with_category_id.csv", "products_with_category_id.csv"
)
