class ScoreCombiner:
    def __init__(self):
        self.weights = {
            "url_match": 0.3,
            "product_search": 0.5,
            "store_desc": 0.2
        }

    def compute(self, url_match: bool, product_search: bool, store_desc: bool) -> float:
        score = (
            self.weights["url_match"] * int(url_match) +
            self.weights["product_search"] * int(product_search) +
            self.weights["store_desc"] * int(store_desc)
        )
        return round(score, 2)
