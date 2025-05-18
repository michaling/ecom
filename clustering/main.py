from products_recommender import ProductRecommender


def main():
    # Initialize the product recommender
    recommender = ProductRecommender(
        product_file="data/products.csv",
        classifier_file="clustering/saved_models/product_category_classifier.joblib"
    )

    print("\n=== Product Recommendation System ===")
    while True:
        # Ask user for input
        input_product = input("\nEnter a product name (or type 'exit' to quit): ").strip()
        if input_product.lower() == 'exit':
            print("Goodbye!")
            break
        # Find similar products
        recommendations = recommender.find_similar_products(input_product, top_k=5)
        # Show results
        print("\nRecommended similar products:")
        for idx, product in enumerate(recommendations, 1):
            print(f"{idx}. {product}")

if __name__ == "__main__":
    main()

