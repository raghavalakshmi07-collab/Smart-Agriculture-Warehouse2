# =========================================================
# ORDER FULFILLMENT WORKFLOW
# =========================================================


WORKFLOW = [

    "Created",

    "Allocated",

    "Picking",

    "Picked",

    "Packed",

    "Quality Checked",

    "Dispatched"

]


# =========================================================
# NEXT STATUS
# =========================================================

def get_next_status(current_status):

    if current_status not in WORKFLOW:

        return None


    index = WORKFLOW.index(
        current_status
    )


    if index == len(WORKFLOW) - 1:

        return None


    return WORKFLOW[index + 1]


# =========================================================
# UPDATE FULFILLMENT STATUS
# =========================================================

def update_fulfillment(
    conn,
    order_id,
    new_status
):

    if new_status not in WORKFLOW:

        return False, "Invalid status."


    order = conn.execute("""
        SELECT status

        FROM orders

        WHERE order_id = ?
    """, (order_id,)).fetchone()


    if order is None:

        return False, "Order not found."


    current_status = order["status"]


    current_index = WORKFLOW.index(
        current_status
    )

    new_index = WORKFLOW.index(
        new_status
    )


    # Don't allow jumping backwards

    if new_index < current_index:

        return False, (
            "Order cannot move backwards "
            "in the fulfillment workflow."
        )


    conn.execute("""
        UPDATE orders

        SET status = ?

        WHERE order_id = ?
    """, (

        new_status,

        order_id

    ))


    conn.commit()


    return True, (
        f"Order {order_id} moved to "
        f"{new_status}."
    )