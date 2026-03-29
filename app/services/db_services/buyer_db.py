def find_buyer_by_account_id(db, customer_assigned_account_id):
    query = """
        SELECT buyer_id FROM buyers
        WHERE customer_assigned_account_id = %(customer_assigned_account_id)s
    """
    return db.execute_query(query, {"customer_assigned_account_id": customer_assigned_account_id})

def insert_buyer_tax_scheme(db, tax_scheme):
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