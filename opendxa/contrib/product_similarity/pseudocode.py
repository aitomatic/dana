def in_stock(product):
    return product.inventory > 0


def find_similar_products(product, use_case_description, top_k=10):
    candidates = use("product_vector_search", input={"query": product.description, "top_k": 5 * top_k})
    filtered_candidates = filter(candidates, in_stock)

    scores = []
    for candidate in filtered_candidates:
        analysis = {
            "high_retention": candidate.retention >= 0.9,
            "matched_category": candidate.category == product.category,
            "same_purpose": reason(
                "Do these products serve the same purpose for this use case?",
                return_type=bool,
                context=[product, candidate, use_case_description],
            ),
            "used_together": reason(
                "Are these products often used together in this use case?",
                return_type=bool,
                context=[product, candidate, use_case_description],
            ),
            "differences": reason(
                "What could be functional differences between these products for this use case?",
                return_type=str,
                context=[product, candidate, use_case_description],
            ),
        }
        score = reason(
            "Score this product 0-100 based on how well it would function as an alternative to the original product for this use case",
            return_type=int,
            context=[product, candidate, analysis, use_case_description],
        )
        scores.append((candidate, score))

    return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]
