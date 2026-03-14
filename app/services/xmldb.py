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


def xml_to_db_update_cancel(db, xml, order_id):

    query = """
        INSERT INTO order_documents (
            order_id,
            xml_content,
            document_version
        )
        VALUES (
            %(order_id)s,
            %(xml_content)s,
            1
        )
        ON CONFLICT (order_id)
        DO UPDATE SET
            xml_content      = EXCLUDED.xml_content,
            document_version = order_documents.document_version + 1
    """

    params = {
        "order_id": order_id,
        "xml_content": xml,
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

    xml_data = result[0]

    if isinstance(xml_data, memoryview):
        return bytes(xml_data).decode("utf-8")
    elif isinstance(xml_data, bytes):
        return xml_data.decode("utf-8")
    elif isinstance(xml_data, str) and xml_data.startswith("\\x"):
        return bytes.fromhex(xml_data[2:]).decode("utf-8")
    else:
        return xml_data
