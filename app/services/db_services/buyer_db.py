def find_buyer_by_account_id(db, customer_assigned_account_id):
    query = """
        SELECT buyer_id FROM buyers
        WHERE customer_assigned_account_id = %(customer_assigned_account_id)s
    """
    return db.execute_query(query, {"customer_assigned_account_id": customer_assigned_account_id})

def insert_tax_scheme(db, tax_scheme):
    query = """
        INSERT INTO tax_schemes (
            registration_name,
            company_id,
            exemption_reason,
            scheme_id,
            tax_type_code
        )
        VALUES (
            %(registration_name)s,
            %(company_id)s,
            %(exemption_reason)s,
            %(scheme_id)s,
            %(tax_type_code)s
        )
        RETURNING tax_scheme_id
    """
    return db.execute_insert_update_delete(query, tax_scheme)


def insert_buyer(db, data, address_id, tax_scheme_id):
    query = """
        INSERT INTO buyers (
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
        RETURNING buyer_id
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

def get_buyer_by_id(db, buyer_id):
    query = """
        SELECT
            b.buyer_id,
            b.customer_assigned_account_id,
            b.supplier_assigned_account_id,
            b.party_name,
            b.contact_name,
            b.contact_telephone,
            b.contact_telefax,
            b.contact_email,
            b.tax_scheme_id,
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
        FROM buyers b
        LEFT JOIN addresses a ON b.address_id = a.address_id
        LEFT JOIN tax_schemes t ON b.tax_scheme_id = t.tax_scheme_id
        WHERE b.buyer_id = %(buyer_id)s
    """
    result = db.execute_query(query, {"buyer_id": buyer_id})
    if not result:
        return None

    return {
        "buyer_id":                      str(result[0]),
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
    
def get_buyers_by_api_key(db, api_key):
    query = """
        SELECT b.buyer_id, b.party_name, b.customer_assigned_account_id, b.contact_name, b.contact_email  
        FROM buyers b
        JOIN auth a ON b.buyer_id::text = a.buyer_id
        WHERE a.api_key = %(api_key)s
    """
    return db.execute_query(query, {"api_key": api_key}, fetch_all=True)

def insert_auth(db, api_key, buyer_id):
    query = """
        INSERT INTO auth (api_key, buyer_id)
        VALUES (%(api_key)s, %(buyer_id)s)
        ON CONFLICT (api_key, buyer_id) DO NOTHING
    """

    db.execute_insert_update_delete(query, {
        "api_key": api_key,
        "buyer_id": str(buyer_id)
    })

def validate_buyer_ownership(db, api_key, buyer_id):
    query = """
        SELECT 1 FROM auth
        WHERE api_key = %(api_key)s
        AND buyer_id = %(buyer_id)s
    """

    return db.execute_query(query, {
        "api_key": api_key,
        "buyer_id": str(buyer_id)
    })

def update_buyer(db, buyer_id, data, address_id=None, tax_scheme_id=None):
    fields = []
    params = {"buyer_id": str(buyer_id)}

    if "customer_assigned_account_id" in data:
        fields.append("customer_assigned_account_id = %(customer_assigned_account_id)s")
        params["customer_assigned_account_id"] = data.get("customer_assigned_account_id")

    if "supplier_assigned_account_id" in data:
        fields.append("supplier_assigned_account_id = %(supplier_assigned_account_id)s")
        params["supplier_assigned_account_id"] = data.get("supplier_assigned_account_id")

    if "party_name" in data:
        fields.append("party_name = %(party_name)s")
        params["party_name"] = data.get("party_name")

    if address_id is not None:
        fields.append("address_id = %(address_id)s")
        params["address_id"] = address_id

    if tax_scheme_id is not None:
        fields.append("tax_scheme_id = %(tax_scheme_id)s")
        params["tax_scheme_id"] = tax_scheme_id

    contact = data.get("contact")
    if contact:
        if "name" in contact:
            fields.append("contact_name = %(contact_name)s")
            params["contact_name"] = contact.get("name")

        if "telephone" in contact:
            fields.append("contact_telephone = %(contact_telephone)s")
            params["contact_telephone"] = contact.get("telephone")

        if "telefax" in contact:
            fields.append("contact_telefax = %(contact_telefax)s")
            params["contact_telefax"] = contact.get("telefax")

        if "email" in contact:
            fields.append("contact_email = %(contact_email)s")
            params["contact_email"] = contact.get("email")

    if not fields:
        return False

    query = f"""
        UPDATE buyers
        SET {", ".join(fields)}
        WHERE buyer_id = %(buyer_id)s
    """

    db.execute_insert_update_delete(query, params)
    return True


def buyer_has_existing_orders(db, buyer_id):
    query = """
        SELECT 1
        FROM orders
        WHERE buyer_id = %(buyer_id)s
        LIMIT 1
    """
    result = db.execute_query(query, {"buyer_id": str(buyer_id)})
    return bool(result)


def delete_buyer(db, buyer_id):
    query = """
        DELETE FROM buyers
        WHERE buyer_id = %(buyer_id)s
        RETURNING buyer_id
    """
    return db.execute_insert_update_delete(query, {"buyer_id": str(buyer_id)})

def get_buyers_by_seller_id(db, seller_id):
    query = """
        SELECT
            b.buyer_id,
            b.customer_assigned_account_id,
            b.supplier_assigned_account_id,
            b.party_name,
            b.contact_name,
            b.contact_telephone,
            b.contact_telefax,
            b.contact_email,

            t.tax_scheme_id,
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

        FROM buyer_seller bs
        JOIN buyers b ON bs.buyer_id = b.buyer_id
        LEFT JOIN tax_schemes t ON b.tax_scheme_id = t.tax_scheme_id
        LEFT JOIN addresses a ON b.address_id = a.address_id
        WHERE bs.seller_id = %(seller_id)s
    """

    return db.execute_query(query, {"seller_id": seller_id}, fetch_all=True)


def insert_buyer_seller(db, buyer_id, seller_id):
    query = """
        INSERT INTO buyer_seller (buyer_id, seller_id)
        VALUES (%(buyer_id)s, %(seller_id)s)
        ON CONFLICT (buyer_id, seller_id) DO NOTHING
        RETURNING id
    """
    return db.execute_insert_update_delete(query, {
        "buyer_id": str(buyer_id),
        "seller_id": str(seller_id)
    })
    
    
def delete_buyer_seller(db, buyer_id, seller_id):
    query = """
        DELETE FROM buyer_seller
        WHERE buyer_id = %(buyer_id)s
        AND seller_id = %(seller_id)s
        RETURNING id
    """
    return db.execute_insert_update_delete(query, {
        "buyer_id": str(buyer_id),
        "seller_id": str(seller_id)
    })
    
def buyer_seller_exists(db, buyer_id, seller_id):
    query = """
        SELECT 1 FROM buyer_seller
        WHERE buyer_id = %(buyer_id)s
        AND seller_id = %(seller_id)s
    """
    return db.execute_query(query, {
        "buyer_id": str(buyer_id),
        "seller_id": str(seller_id)
    })