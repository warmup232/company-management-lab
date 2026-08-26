from flask import Flask, jsonify, request
import mysql.connector
from config import Config

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok"
    })


@app.route("/products", methods=["GET"])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            product_id,
            product_name,
            price,
            stock_quantity,
            category,
            created_at,
            updated_at
        FROM products
        ORDER BY product_id DESC
    """)

    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(products)


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            product_id,
            product_name,
            price,
            stock_quantity,
            category,
            created_at,
            updated_at
        FROM products
        WHERE product_id = %s
    """, (product_id,))

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if product is None:
        return jsonify({
            "error": "Product not found"
        }), 404

    return jsonify(product)


@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json()

    required_fields = [
        "product_name",
        "price",
        "stock_quantity",
        "category"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"{field} is required"
            }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO products
        (product_name, price, stock_quantity, category)
        VALUES (%s, %s, %s, %s)
    """, (
        data["product_name"],
        data["price"],
        data["stock_quantity"],
        data["category"]
    ))

    conn.commit()

    product_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Product created",
        "product_id": product_id
    }), 201


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE products
        SET
            product_name = %s,
            price = %s,
            stock_quantity = %s,
            category = %s
        WHERE product_id = %s
    """, (
        data.get("product_name"),
        data.get("price"),
        data.get("stock_quantity"),
        data.get("category"),
        product_id
    ))

    conn.commit()

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()

        return jsonify({
            "error": "Product not found"
        }), 404

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Product updated"
    })


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM products
        WHERE product_id = %s
    """, (product_id,))

    conn.commit()

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()

        return jsonify({
            "error": "Product not found"
        }), 404

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Product deleted"
    })


@app.route("/products/<int:product_id>/stock/in", methods=["POST"])
def stock_in(product_id):
    data = request.get_json()
    quantity = data.get("quantity")

    if not quantity or quantity <= 0:
        return jsonify({
            "error": "Quantity must be greater than 0"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE products
        SET stock_quantity = stock_quantity + %s
        WHERE product_id = %s
    """, (quantity, product_id))

    if cursor.rowcount == 0:
        cursor.close()
        conn.close()

        return jsonify({
            "error": "Product not found"
        }), 404

    cursor.execute("""
        INSERT INTO stock_transactions
        (product_id, transaction_type, quantity)
        VALUES (%s, 'IN', %s)
    """, (product_id, quantity))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Stock added",
        "quantity": quantity
    })


@app.route("/products/<int:product_id>/stock/out", methods=["POST"])
def stock_out(product_id):
    data = request.get_json()
    quantity = data.get("quantity")

    if not quantity or quantity <= 0:
        return jsonify({
            "error": "Quantity must be greater than 0"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT stock_quantity
        FROM products
        WHERE product_id = %s
    """, (product_id,))

    product = cursor.fetchone()

    if product is None:
        cursor.close()
        conn.close()

        return jsonify({
            "error": "Product not found"
        }), 404

    if product["stock_quantity"] < quantity:
        cursor.close()
        conn.close()

        return jsonify({
            "error": "Insufficient stock"
        }), 400

    cursor.execute("""
        UPDATE products
        SET stock_quantity = stock_quantity - %s
        WHERE product_id = %s
    """, (quantity, product_id))

    cursor.execute("""
        INSERT INTO stock_transactions
        (product_id, transaction_type, quantity)
        VALUES (%s, 'OUT', %s)
    """, (product_id, quantity))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Stock removed",
        "quantity": quantity
    })


@app.route("/products/low-stock", methods=["GET"])
def low_stock():
    threshold = request.args.get("threshold", default=10, type=int)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            product_id,
            product_name,
            stock_quantity,
            category
        FROM products
        WHERE stock_quantity <= %s
        ORDER BY stock_quantity ASC
    """, (threshold,))

    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(products)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
