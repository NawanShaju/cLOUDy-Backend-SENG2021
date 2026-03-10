from database.PostgresDB import PostgresDB

def xml_to_db(db, xml, order_id):

    query = """
        INSERT INTO order_documents (
            order_id,
            xml_content,
            document_version
        )
        VALUES (
            %(order_id)s,
            %(xml_content)s,
            %(document_version)s
        )
    """

    params = {
        "order_id": order_id,
        "xml_content": xml,
        "document_version": 1,
    }

    db.execute_insert_update_delete(query, params)

def get_order_xml(db, order_id):
    query = """
        SELECT xml_content
        FROM order_documents
        WHERE order_id = %(order_id)s
    """

    params = {
        "order_id": order_id
    }

    result = db.execute_query(query, params)

    if not result:
        return None

    return result[0]