# =========================================================
# EXCEPTION MANAGEMENT
# =========================================================


# =========================================================
# REPORT DAMAGED ITEM
# =========================================================

def report_damaged_item(

    conn,

    product_id,

    quantity,

    reason

):

    conn.execute("""
        INSERT INTO damaged_items
        (
            product_id,
            quantity,
            reason,
            status
        )

        VALUES (?, ?, ?, ?)
    """, (

        product_id,

        quantity,

        reason,

        "Open"

    ))


    # Increase damaged quantity

    conn.execute("""
        UPDATE inventory

        SET damaged =
            damaged + ?

        WHERE product_id = ?
    """, (

        quantity,

        product_id

    ))


    conn.commit()


    return {

        "success": True,

        "message":
        "Damaged item recorded successfully."

    }


# =========================================================
# GET OPEN EXCEPTIONS
# =========================================================

def get_open_exceptions(conn):

    return conn.execute("""
        SELECT *

        FROM damaged_items

        WHERE status = 'Open'

        ORDER BY id DESC
    """).fetchall()


# =========================================================
# RESOLVE EXCEPTION
# =========================================================

def resolve_exception(

    conn,

    exception_id

):

    exception = conn.execute("""
        SELECT *

        FROM damaged_items

        WHERE id = ?
    """, (exception_id,)).fetchone()


    if exception is None:

        return False, (
            "Exception not found."
        )


    conn.execute("""
        UPDATE damaged_items

        SET status = 'Resolved'

        WHERE id = ?
    """, (exception_id,))


    conn.commit()


    return True, (
        "Exception resolved successfully."
    )