from products_recommender import ProductRecommender
from list_based_recommender import ListBasedRecommender


def main():
    # Initialize the product recommender
    recommender = ProductRecommender()

    # Initialize the list-based recommender
    list_recommender = ListBasedRecommender()

    print("\n=== Product Recommendation System ===")
    print("Choose mode:\n1. Product-based\n2. List-based")

    while True:
        mode = input("\nSelect mode (1 or 2), or type 'exit': ").strip()
        if mode.lower() == 'exit':
            print("Goodbye!")
            break

        if mode == "1":
            input_product = input("Enter a product name: ").strip()
            recommendations = recommender.find_similar_products(input_product, top_k=5)

            print("\nRecommended similar products:")
            for idx, product in enumerate(recommendations, 1):
                print(f"{idx}. {product}")

        elif mode == "2":
            input_list = input("Enter a list name: ").strip()
            recommendations = list_recommender.recommend_from_list_name(input_list)

            print("\nRecommended products from similar lists:")
            for idx, product in enumerate(recommendations, 1):
                print(f"{idx}. {product}")

        else:
            print("Invalid selection. Please choose '1', '2', or 'exit'.")

if __name__ == "__main__":
    main()
