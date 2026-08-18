# =========================================================
# PICKING MANAGEMENT
# =========================================================

from logic.priority import sort_orders_by_priority


# =========================================================
# GET PICKING QUEUE
# =========================================================

def get_picking_queue(conn):

    orders = conn.execute("""
        SELECT
            order_id,
            customer,
            priority,
            status

        FROM orders

        WHERE status IN
        (
            'Allocated',
            'Picking'
        )
    """).fetchall()


    orders = [

        dict(order)

        for order in orders

    ]


    return sort_orders_by_priority(
        orders
    )


# =========================================================
# START PICKING
# =========================================================

def start_picking(conn, order_id):

    order = conn.execute("""
        SELECT *
        FROM orders
        WHERE order_id = ?
    """, (order_id,)).fetchone()


    if order is None:

        return False, "Order not found."


    conn.execute("""
        UPDATE orders

        SET status = 'Picking'

        WHERE order_id = ?
    """, (order_id,))


    conn.commit()


    return True, (
        f"Picking started for {order_id}."
    )


# =========================================================
# COMPLETE PICKING
# =========================================================

def complete_picking(conn, order_id):

    conn.execute("""
        UPDATE orders

        SET status = 'Picked'

        WHERE order_id = ?
    """, (order_id,))


    conn.commit()


    return True, (
        f"Order {order_id} picking completed."
    )