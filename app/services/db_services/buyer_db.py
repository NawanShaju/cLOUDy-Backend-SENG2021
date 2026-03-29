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

    row = result
    return {
        "buyer_id":                      str(row[0]),
        "customer_assigned_account_id":  row[1],
        "supplier_assigned_account_id":  row[2],
        "party_name":                    row[3],
        "contact": {
            "name":      row[4],
            "telephone": row[5],
            "telefax":   row[6],
            "email":     row[7],
        },
        "tax_scheme": {
            "registration_name": row[9],
            "company_id":        row[10],
            "exemption_reason":  row[11],
            "scheme_id":         row[12],
            "tax_type_code":     row[13],
        } if row[8] else None,
        "address": {
            "street":       row[14],
            "city":         row[15],
            "state":        row[16],
            "postal_code":  row[17],
            "country_code": row[18],
        } if row[14] else None,
    }
    