import pandas as pd

# Paths to the CSV files
existing_file = 'products.csv'  # Replace with your file path
new_file = 'supermarket_products.csv'  # New file generated
output_file = 'products.csv'  # The merged file name

# Read both CSV files
existing_df = pd.read_csv(existing_file)
new_df = pd.read_csv(new_file)

# Append the new file to the existing file
merged_df = pd.concat([existing_df, new_df], ignore_index=True)

# Save the merged DataFrame to a new CSV file
merged_df.to_csv(output_file, index=False)