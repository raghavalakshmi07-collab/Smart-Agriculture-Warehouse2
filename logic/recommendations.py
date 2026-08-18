# =========================================================
# SMART RECOMMENDATIONS
# =========================================================


def reorder_recommendations(conn):

    products = conn.execute("""
        SELECT

            i.product_id,

            p.name,

            i.quantity,

            i.damaged,

            p.reorder_level

        FROM inventory i

        JOIN products p

        ON i.product_id = p.product_id

    """).fetchall()


    recommendations = []


    for product in products:

        usable = (

            product["quantity"]

            - product["damaged"]

        )


        reorder_level = (
            product["reorder_level"]
        )


        # =================================================
        # LOW STOCK
        # =================================================

        if usable <= reorder_level:

            # Recommended quantity
            # = 2 × reorder level - usable stock

            suggested = (

                reorder_level * 2

            ) - usable


            if suggested < 1:

                suggested = 1


            recommendations.append({

                "product_id":
                product["product_id"],

                "name":
                product["name"],

                "usable":
                usable,

                "reorder_level":
                reorder_level,

                "suggested":
                suggested

            })


    return recommendations


# =========================================================
# CHECK PRODUCT REORDER NEED
# =========================================================

def needs_reorder(

    usable_stock,

    reorder_level

):

    return usable_stock <= reorder_level