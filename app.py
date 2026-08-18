from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import csv
import os

from logic.inventory import get_inventory, low_stock_items
from logic.allocation import allocate_order
from logic.recommendations import reorder_recommendations


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = "smart-warehouse-secret-key"

DATABASE = "database.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

def init_db():

    conn = get_db()

    conn.executescript("""

    CREATE TABLE IF NOT EXISTS products (

        product_id TEXT PRIMARY KEY,

        name TEXT NOT NULL,

        category TEXT,

        unit TEXT,

        reorder_level INTEGER

    );


    CREATE TABLE IF NOT EXISTS inventory (

        product_id TEXT PRIMARY KEY,

        location_id TEXT,

        quantity INTEGER,

        damaged INTEGER DEFAULT 0

    );


    CREATE TABLE IF NOT EXISTS orders (

        order_id TEXT PRIMARY KEY,

        customer TEXT,

        priority TEXT,

        status TEXT,

        order_date TEXT

    );


    CREATE TABLE IF NOT EXISTS order_items (

        order_id TEXT,

        product_id TEXT,

        quantity INTEGER

    );


    CREATE TABLE IF NOT EXISTS locations (

        location_id TEXT PRIMARY KEY,

        zone TEXT,

        shelf TEXT,

        bin TEXT

    );


    CREATE TABLE IF NOT EXISTS employees (

        employee_id TEXT PRIMARY KEY,

        name TEXT,

        role TEXT

    );


    CREATE TABLE IF NOT EXISTS damaged_items (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        product_id TEXT,

        quantity INTEGER,

        reason TEXT,

        status TEXT

    );

    """)

    conn.commit()

    conn.close()


# ============================================================
# LOAD CSV DATA
# ============================================================

def load_csv_data():

    conn = get_db()

    tables = [

        "products",
        "inventory",
        "orders",
        "order_items",
        "locations",
        "employees",
        "damaged_items"

    ]

    for table in tables:

        file_path = os.path.join(
            "data",
            table + ".csv"
        )

        if not os.path.exists(file_path):

            print(
                f"CSV file not found: {file_path}"
            )

            continue

        with open(
            file_path,
            "r",
            encoding="utf-8",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            rows = list(reader)

        if not rows:
            continue

        columns = list(
            rows[0].keys()
        )

        placeholders = ",".join(
            ["?"] * len(columns)
        )

        query = f"""
        INSERT OR IGNORE INTO {table}
        ({','.join(columns)})
        VALUES ({placeholders})
        """

        for row in rows:

            values = [
                row[column]
                for column in columns
            ]

            conn.execute(
                query,
                values
            )

    conn.commit()

    conn.close()

    print("CSV data loaded successfully.")


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return redirect(
        url_for("dashboard")
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        if username and password:

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Please enter username and password.",
            "warning"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    conn = get_db()

    total_products = conn.execute(
        """
        SELECT COUNT(*)
        FROM products
        """
    ).fetchone()[0]

    total_orders = conn.execute(
        """
        SELECT COUNT(*)
        FROM orders
        """
    ).fetchone()[0]

    pending_orders = conn.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status != 'Dispatched'
        """
    ).fetchone()[0]

    low_stock = len(
        low_stock_items(conn)
    )

    recent_orders = conn.execute(
        """
        SELECT *
        FROM orders
        ORDER BY order_date DESC
        LIMIT 10
        """
    ).fetchall()

    conn.close()

    stats = {

        "products": total_products,

        "orders": total_orders,

        "pending": pending_orders,

        "low_stock": low_stock

    }

    return render_template(

        "dashboard.html",

        stats=stats,

        recent=recent_orders

    )


# ============================================================
# PRODUCTS
# ============================================================

@app.route("/products")
def products():

    conn = get_db()

    products_data = conn.execute(
        """
        SELECT *
        FROM products
        ORDER BY product_id
        """
    ).fetchall()

    conn.close()

    return render_template(

        "products.html",

        products=products_data

    )


# ============================================================
# INVENTORY
# ============================================================

@app.route("/inventory")
def inventory():

    conn = get_db()

    inventory_data = get_inventory(
        conn
    )

    low_stock = low_stock_items(
        conn
    )

    conn.close()

    return render_template(

        "inventory.html",

        inventory=inventory_data,

        low=low_stock

    )


# ============================================================
# ORDERS
# ============================================================

@app.route("/orders")
def orders():

    conn = get_db()

    orders_data = conn.execute(
        """
        SELECT *
        FROM orders
        ORDER BY order_date DESC
        """
    ).fetchall()

    conn.close()

    return render_template(

        "orders.html",

        orders=orders_data

    )


# ============================================================
# ORDER DETAILS
# ============================================================

@app.route(
    "/orders/<order_id>"
)
def order_details(order_id):

    conn = get_db()

    order = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE order_id = ?
        """,
        (order_id,)
    ).fetchone()

    items = conn.execute(
        """
        SELECT

            oi.order_id,

            oi.product_id,

            oi.quantity,

            p.name,

            i.quantity AS available,

            i.location_id

        FROM order_items oi

        JOIN products p
        ON oi.product_id = p.product_id

        LEFT JOIN inventory i
        ON oi.product_id = i.product_id

        WHERE oi.order_id = ?

        """,
        (order_id,)
    ).fetchall()

    conn.close()

    return render_template(

        "order_details.html",

        order=order,

        items=items

    )


# ============================================================
# SMART INVENTORY ALLOCATION
# ============================================================

@app.route(
    "/orders/<order_id>/allocate",
    methods=["POST"]
)
def allocate(order_id):

    conn = get_db()

    result = allocate_order(

        conn,

        order_id

    )

    conn.close()

    if result["success"]:

        flash(
            result["message"],
            "success"
        )

    else:

        flash(
            result["message"],
            "warning"
        )

    return redirect(

        url_for(
            "order_details",
            order_id=order_id
        )

    )


# ============================================================
# PICKING
# ============================================================

@app.route("/picking")
def picking():

    conn = get_db()

    picking_orders = conn.execute(
        """
        SELECT

            order_id,

            customer,

            priority,

            status

        FROM orders

        WHERE status IN
        (
            'Created',
            'Allocated',
            'Picking'
        )

        ORDER BY

        CASE priority

            WHEN 'Urgent' THEN 1

            WHEN 'High' THEN 2

            WHEN 'Medium' THEN 3

            WHEN 'Low' THEN 4

            ELSE 5

        END

        """
    ).fetchall()

    conn.close()

    return render_template(

        "picking.html",

        orders=picking_orders

    )


# ============================================================
# PACKING
# ============================================================

@app.route("/packing")
def packing():

    conn = get_db()

    packing_orders = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE status = 'Picked'
        """
    ).fetchall()

    conn.close()

    return render_template(

        "packing.html",

        orders=packing_orders

    )


# ============================================================
# DISPATCH
# ============================================================

@app.route("/dispatch")
def dispatch():

    conn = get_db()

    dispatch_orders = conn.execute(
        """
        SELECT *
        FROM orders

        WHERE status IN
        (
            'Packed',
            'Quality Checked'
        )

        """
    ).fetchall()

    conn.close()

    return render_template(

        "dispatch.html",

        orders=dispatch_orders

    )


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@app.route(
    "/orders/<order_id>/status/<status>",
    methods=["POST"]
)
def update_status(
    order_id,
    status
):

    allowed_status = [

        "Picking",

        "Picked",

        "Packed",

        "Quality Checked",

        "Dispatched"

    ]

    if status not in allowed_status:

        flash(
            "Invalid order status.",
            "warning"
        )

        return redirect(
            url_for("orders")
        )

    conn = get_db()

    conn.execute(
        """
        UPDATE orders

        SET status = ?

        WHERE order_id = ?

        """,
        (
            status,
            order_id
        )
    )

    conn.commit()

    conn.close()

    flash(

        f"Order {order_id} moved to {status}.",

        "success"

    )

    return redirect(

        request.referrer

        or url_for("orders")

    )


# ============================================================
# EXCEPTIONS
# ============================================================

@app.route("/exceptions")
def exceptions():

    conn = get_db()

    damaged_items = conn.execute(
        """
        SELECT *

        FROM damaged_items

        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(

        "exceptions.html",

        items=damaged_items

    )


# ============================================================
# ANALYTICS
# ============================================================

@app.route("/analytics")
def analytics():

    conn = get_db()

    status_data = conn.execute(
        """
        SELECT

            status,

            COUNT(*) AS count

        FROM orders

        GROUP BY status

        """
    ).fetchall()

    priority_data = conn.execute(
        """
        SELECT

            priority,

            COUNT(*) AS count

        FROM orders

        GROUP BY priority

        """
    ).fetchall()

    recommendations = reorder_recommendations(
        conn
    )

    conn.close()

    return render_template(

        "analytics.html",

        status=status_data,

        priority=priority_data,

        recommendations=recommendations

    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    # Create tables
    init_db()

    # Load CSV data
    load_csv_data()

    print()
    print("=" * 50)
    print("       SMART WAREHOUSE SYSTEM")
    print("       Agriculture Supplies Warehouse")
    print("=" * 50)
    print()
    print("Server running...")
    print("Open: http://127.0.0.1:5000")
    print()

    app.run(
        debug=True
    )