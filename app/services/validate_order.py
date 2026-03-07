def validate_order(data, buyerId):
    
    if not buyerId:
        return "buyerId is not defined, please provide a valid buyerId"
    
    address = data.get("address")
    
    if not address:
        return "No address provided"

    for field in ["street", "city", "state", "postal_code"]:
        if field not in address:
            return f"the required field {field} is missing"
                
    for date_field in ["order_date", "delivery_date"]:
        date = data.get(date_field)
        
        if not date:
            return f"{date_field} is required"
        
    for field in ["currency_code", "status"]:
        if not data.get(field):
            return f"'{field}' is required."
        
    
    items = data.get("items")
    
    if not items:
        return "no order was provided"
    
    if isinstance(items, dict):
        items = [items]
    
    for item in items:
        if not item.get("item_name"):
            return f"item_name is required."
        if "quantity" not in item or not isinstance(item["quantity"], int) or item["quantity"] <= 0:
            return f"quantity must be a positive integer."
        if "unit_price" not in item or not isinstance(item["unit_price"], (int, float)) or item["unit_price"] < 0:
            return f"unit_price must be a non-negative integer."
    
    