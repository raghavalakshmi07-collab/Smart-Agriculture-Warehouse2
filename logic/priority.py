# =========================================================
# ORDER PRIORITY MANAGEMENT
# =========================================================


PRIORITY_SCORE = {

    "Urgent": 4,

    "High": 3,

    "Medium": 2,

    "Low": 1

}


# =========================================================
# PRIORITY SCORE
# =========================================================

def get_priority_score(priority):

    return PRIORITY_SCORE.get(
        priority,
        1
    )


# =========================================================
# DETERMINE ORDER PRIORITY
# =========================================================

def determine_priority(order):

    """
    Determine priority based on
    order information.
    """

    priority = order.get(
        "priority",
        "Low"
    )

    if priority not in PRIORITY_SCORE:

        priority = "Low"

    return priority


# =========================================================
# SORT ORDERS BY PRIORITY
# =========================================================

def sort_orders_by_priority(orders):

    return sorted(

        orders,

        key=lambda order:
        get_priority_score(
            order["priority"]
        ),

        reverse=True

    )