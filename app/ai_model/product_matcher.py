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

def match_buyer(extracted_buyer, buyers_list):
    best_score = 0
    best_match = None

    extracted_name = extracted_buyer.get("party_name", "")
    extracted_account = extracted_buyer.get("customer_assigned_account_id", "")
    extracted_email = extracted_buyer.get("contact", {}).get("email", "")

    for buyer in buyers_list:
        buyer_name = buyer.get("party_name", "")
        buyer_account = buyer.get("customer_assigned_account_id", "")
        buyer_email = buyer.get("contact_email", "")

        score_name = similarity(extracted_name, buyer_name)
        score_account = similarity(extracted_account, buyer_account)
        score_email = similarity(extracted_email, buyer_email)
        total_score = max(score_name, score_account, score_email)

        if total_score > best_score:
            best_score = total_score
            best_match = buyer

    if best_match and best_score > 0.7:
        return best_match.get("buyerId")

    return None