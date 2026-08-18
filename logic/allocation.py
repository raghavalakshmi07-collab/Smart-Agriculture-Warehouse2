# =========================================================
# SMART INVENTORY ALLOCATION
# =========================================================

from logic.inventory import check_stock


# =========================================================
# ALLOCATE SINGLE ORDER
# =========================================================

def allocate_order(conn, order_id):

    # Get order

    order = conn.execute("""
        SELECT *
        FROM orders
        WHERE order_id = ?
    """, (order_id,)).fetchone()


    if order is None:

        return {

            "success": False,

            "message":
            "Order not found."

        }


    # Get order items

    items = conn.execute("""
        SELECT
            product_id,
            quantity

        FROM order_items

        WHERE order_id = ?
    """, (order_id,)).fetchall()


    if not items:

        return {

            "success": False,

            "message":
            "No items found for this order."

        }


    shortage = []

    allocation = []


    # Check every product

    for item in items:

        available = check_stock(

            conn,

            item["product_id"]

        )


        required = item["quantity"]


        if available >= required:

            allocation.append({

                "product_id":
                item["product_id"],

                "required":
                required,

                "available":
                available,

                "allocated":
                required

            })

        else:

            shortage.append({

                "product_id":
                item["product_id"],

                "required":
                required,

                "available":
                available,

                "shortage":
                required - available

            })


    # =====================================================
    # SHORTAGE FOUND
    # =====================================================

    if shortage:

        if order["priority"] == "Urgent":

            message = (
                "Urgent order has insufficient stock. "
                "System recommends priority replenishment "
                "or partial allocation."
            )

        else:

            message = (
                "Insufficient inventory. "
                "Order is waiting for replenishment."
            )


        return {

            "success": False,

            "message": message,

            "shortage": shortage,

            "allocation": allocation

        }


    # =====================================================
    # ALLOCATION SUCCESS
    # =====================================================

    for item in allocation:

        conn.execute("""
            UPDATE inventory

            SET quantity =
                quantity - ?

            WHERE product_id = ?
        """, (

            item["allocated"],

            item["product_id"]

        ))


    # Update order status

    conn.execute("""
        UPDATE orders

        SET status = 'Allocated'

        WHERE order_id = ?
    """, (order_id,))


    conn.commit()


    return {

        "success": True,

        "message":
        f"Order {order_id} allocated successfully.",

        "allocation":
        allocation

    }


# =========================================================
# CHECK IF ORDER CAN BE FULLY ALLOCATED
# =========================================================

def can_allocate_order(conn, order_id):

    items = conn.execute("""
        SELECT
            product_id,
            quantity

        FROM order_items

        WHERE order_id = ?
    """, (order_id,)).fetchall()


    for item in items:

        available = check_stock(

            conn,

            item["product_id"]

        )


        if available < item["quantity"]:

            return False


    return True