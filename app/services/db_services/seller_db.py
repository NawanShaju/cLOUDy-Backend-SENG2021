def find_seller_by_account_id(db, customer_assigned_account_id):
    query = """
        SELECT seller_id FROM sellers
        WHERE customer_assigned_account_id = %(customer_assigned_account_id)s
    """
    return db.execute_query(query, {"customer_assigned_account_id": customer_assigned_account_id})

def insert_seller(db, data, address_id, tax_scheme_id):
    query = """
        INSERT INTO sellers (
            customer_assigned_account_id,
            supplier_assigned_account_id,
            party_name,
            address_id,
            tax_scheme_id,
            contact_name,
            contact_telephone,
            contact_telefax,
            contact_email
        )
        VALUES (
            %(customer_assigned_account_id)s,
            %(supplier_assigned_account_id)s,
            %(party_name)s,
            %(address_id)s,
            %(tax_scheme_id)s,
            %(contact_name)s,
            %(contact_telephone)s,
            %(contact_telefax)s,
            %(contact_email)s
        )
        RETURNING seller_id
    """
    contact = data.get("contact", {})
    params = {
        "customer_assigned_account_id": data.get("customer_assigned_account_id"),
        "supplier_assigned_account_id": data.get("supplier_assigned_account_id"),
        "party_name":                   data.get("party_name"),
        "address_id":                   address_id,
        "tax_scheme_id":                tax_scheme_id,
        "contact_name":                 contact.get("name"),
        "contact_telephone":            contact.get("telephone"),
        "contact_telefax":              contact.get("telefax"),
        "contact_email":                contact.get("email"),
    }
    return db.execute_insert_update_delete(query, params)

def get_seller_by_id(db, seller_id):
    query = """
        SELECT
            s.seller_id,
            s.customer_assigned_account_id,
            s.supplier_assigned_account_id,
            s.party_name,
            s.contact_name,
            s.contact_telephone,
            s.contact_telefax,
            s.contact_email,
            s.tax_scheme_id,
            t.registration_name,
            t.company_id,
            t.exemption_reason,
            t.scheme_id,
            t.tax_type_code,
            a.street,
            a.city,
            a.state,
            a.postal_code,
            a.country_code
        FROM sellers s
        LEFT JOIN addresses a ON s.address_id = a.address_id
        LEFT JOIN tax_schemes t ON s.tax_scheme_id = t.tax_scheme_id
        WHERE s.seller_id = %(seller_id)s
    """
    result = db.execute_query(query, {"seller_id": seller_id})
    if not result:
        return None

    return {
        "seller_id":                     str(result[0]),
        "customer_assigned_account_id":  result[1],
        "supplier_assigned_account_id":  result[2],
        "party_name":                    result[3],
        "contact": {
            "name":      result[4],
            "telephone": result[5],
            "telefax":   result[6],
            "email":     result[7],
        },
        "tax_scheme": {
            "registration_name": result[9],
            "company_id":        result[10],
            "exemption_reason":  result[11],
            "scheme_id":         result[12],
            "tax_type_code":     result[13],
        } if result[8] else None,
        "address": {
            "street":       result[14],
            "city":         result[15],
            "state":        result[16],
            "postal_code":  result[17],
            "country_code": result[18],
        } if result[14] else None,
    }

def get_all_sellers(db):
    query = """
        SELECT seller_id, party_name, customer_assigned_account_id
        FROM sellers
    """
    return db.execute_query(query, {}, fetch_all=True)