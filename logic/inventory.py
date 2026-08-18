# =========================================================
# INVENTORY MANAGEMENT
# =========================================================


def get_inventory(conn):
    """
    Get complete inventory information.
    """

    inventory = conn.execute("""
        SELECT
            i.product_id,
            p.name,
            p.category,
            i.location_id,
            i.quantity,
            i.damaged,
            p.reorder_level,

            (i.quantity - i.damaged)
            AS usable_quantity

        FROM inventory i

        JOIN products p
        ON i.product_id = p.product_id

        ORDER BY i.product_id
    """).fetchall()

    return inventory


# =========================================================
# LOW STOCK DETECTION
# =========================================================

def low_stock_items(conn):
    """
    Find products which are below
    or equal to reorder level.
    """

    low_stock = conn.execute("""
        SELECT
            i.product_id,
            p.name,
            i.quantity,
            i.damaged,
            p.reorder_level,

            (i.quantity - i.damaged)
            AS usable_quantity

        FROM inventory i

        JOIN products p
        ON i.product_id = p.product_id

        WHERE
            (i.quantity - i.damaged)
            <= p.reorder_level

        ORDER BY usable_quantity
    """).fetchall()

    return low_stock


# =========================================================
# OUT OF STOCK
# =========================================================

def out_of_stock_items(conn):
    """
    Find products with zero usable stock.
    """

    items = conn.execute("""
        SELECT
            i.product_id,
            p.name,
            i.quantity,
            i.damaged,

            (i.quantity - i.damaged)
            AS usable_quantity

        FROM inventory i

        JOIN products p
        ON i.product_id = p.product_id

        WHERE
            (i.quantity - i.damaged) <= 0

        ORDER BY p.name
    """).fetchall()

    return items


# =========================================================
# STOCK AVAILABILITY
# =========================================================

def check_stock(conn, product_id):

    item = conn.execute("""
        SELECT
            quantity,
            damaged,
            (quantity - damaged)
            AS usable_quantity

        FROM inventory

        WHERE product_id = ?
    """, (product_id,)).fetchone()

    if item is None:

        return 0

    return item["usable_quantity"]