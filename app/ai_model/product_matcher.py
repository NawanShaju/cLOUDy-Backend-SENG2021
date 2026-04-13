from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def match_products_with_quantity(extracted_products, seller_products):
    matched = []

    for candidate in extracted_products:
        product_name = candidate.get("product_name", "")

        quantity = candidate.get("quantity", "")

        best_score = 0
        best_match = None

        for product in seller_products:
            score = similarity(product_name, product["productName"])

            if score > best_score:
                best_score = score
                best_match = product

        if best_match and best_score > 0.6:
            matched.append([best_match["productId"], quantity])

    return matched