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


def xml_to_db_update_delete(db, xml, order_id):

    query = """
        INSERT INTO order_documents (
            order_id,
            xml_content,
            document_version
        )
        VALUES (
            %(order_id)s,
            %(xml_content)s,
            (
                SELECT COALESCE(MAX(document_version), 0) + 1
                FROM order_documents
                WHERE order_id = %(order_id)s
            )
        )
    """

    params = {
        "order_id": order_id,
        "xml_content": xml,
    }

    db.execute_insert_update_delete(query, params)