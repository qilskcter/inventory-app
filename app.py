import logging

import psycopg2
import psycopg2.extras
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from init_db import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = "supersecretkey"

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Request body phải là JSON object hợp lệ.", 400)
    return data


def _validate_product_fields(data, allowed_fields, required_fields=()):
    unknown_fields = set(data) - set(allowed_fields)
    if unknown_fields:
        raise ApiError(
            f"Trường không được hỗ trợ: {', '.join(sorted(unknown_fields))}.", 400
        )

    missing_fields = set(required_fields) - set(data)
    if missing_fields:
        raise ApiError(
            f"Thiếu trường bắt buộc: {', '.join(sorted(missing_fields))}.", 400
        )

    validated = {}
    for field in ("sku", "name"):
        if field in data:
            value = data[field]
            if not isinstance(value, str) or not value.strip():
                raise ApiError(f"'{field}' phải là chuỗi không được để trống.", 400)
            validated[field] = value.strip()

    for field in ("quantity", "min_threshold"):
        if field in data:
            value = data[field]
            if type(value) is not int or value < 0:
                raise ApiError(f"'{field}' phải là số nguyên không âm.", 400)
            validated[field] = value

    return validated


def _row_dict(row):
    return dict(row) if row is not None else None


def _get_product(product_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            return _row_dict(cur.fetchone())
        finally:
            cur.close()
    finally:
        conn.close()


def _perform_stock_transaction(product_id, trans_type, quantity):
    if trans_type not in ("IN", "OUT"):
        raise ApiError("'type' chỉ nhận giá trị 'IN' hoặc 'OUT'.", 400)
    if type(quantity) is not int or quantity <= 0:
        raise ApiError("'quantity' phải là số nguyên dương.", 400)

    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            if trans_type == "IN":
                cur.execute(
                    """
                    UPDATE products
                    SET quantity = quantity + %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING *
                    """,
                    (quantity, product_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE products
                    SET quantity = quantity - %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND quantity >= %s
                    RETURNING *
                    """,
                    (quantity, product_id, quantity),
                )

            product = _row_dict(cur.fetchone())
            if product is None:
                cur.execute("SELECT id FROM products WHERE id = %s", (product_id,))
                if cur.fetchone() is None:
                    raise ApiError("Không tìm thấy sản phẩm.", 404)
                raise ApiError("Số lượng xuất vượt quá tồn kho hiện tại.", 409)

            cur.execute(
                """
                INSERT INTO transactions (product_id, type, quantity)
                VALUES (%s, %s, %s)
                RETURNING id, product_id, type, quantity, created_at
                """,
                (product_id, trans_type, quantity),
            )
            transaction = _row_dict(cur.fetchone())
            conn.commit()
            return product, transaction
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()


@app.errorhandler(ApiError)
def handle_api_error(error):
    return jsonify({"error": error.message}), error.status_code


@app.errorhandler(psycopg2.IntegrityError)
def handle_integrity_error(error):
    logger.info("Database constraint rejected request: %s", error)
    return jsonify({"error": "SKU đã tồn tại hoặc dữ liệu vi phạm ràng buộc."}), 409


@app.errorhandler(psycopg2.OperationalError)
def handle_database_operational_error(error):
    logger.exception("Database operation failed")
    if request.path.startswith("/api/"):
        return (
            jsonify({"error": "Cơ sở dữ liệu tạm thời không khả dụng. Vui lòng thử lại."}),
            503,
            {"Retry-After": "5"},
        )
    return render_template("service_unavailable.html"), 503, {"Retry-After": "5"}


@app.route("/")
def index():
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute("SELECT * FROM products ORDER BY id ASC;")
            products = cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()
    return render_template("index.html", products=products)


@app.route("/add", methods=["POST"])
def add_product():
    try:
        quantity = int(request.form["quantity"])
        min_threshold = int(request.form["min_threshold"])
        data = _validate_product_fields(
            {
                "sku": request.form["sku"],
                "name": request.form["name"],
                "quantity": quantity,
                "min_threshold": min_threshold,
            },
            ("sku", "name", "quantity", "min_threshold"),
            ("sku", "name", "quantity", "min_threshold"),
        )
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO products (sku, name, quantity, min_threshold)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        data["sku"],
                        data["name"],
                        data["quantity"],
                        data["min_threshold"],
                    ),
                )
                conn.commit()
                flash("Thêm sản phẩm thành công!", "success")
            finally:
                cur.close()
        finally:
            conn.close()
    except (KeyError, ValueError, ApiError) as error:
        flash(
            error.message if isinstance(error, ApiError) else "Dữ liệu sản phẩm không hợp lệ.",
            "danger",
        )
    except psycopg2.IntegrityError:
        flash("SKU đã tồn tại hoặc dữ liệu vi phạm ràng buộc.", "danger")
    return redirect(url_for("index"))


@app.route("/transaction", methods=["POST"])
def transaction():
    try:
        product_id = int(request.form["product_id"])
        quantity = int(request.form["quantity"])
        product, _ = _perform_stock_transaction(
            product_id, request.form["type"], quantity
        )
        if product["quantity"] <= product["min_threshold"]:
            flash(
                f"CẢNH BÁO: Sản phẩm '{product['name']}' đang dưới ngưỡng an toàn "
                f"(Còn lại: {product['quantity']})!",
                "warning",
            )
        else:
            flash("Giao dịch thành công!", "success")
    except (KeyError, ValueError, ApiError) as error:
        flash(
            error.message if isinstance(error, ApiError) else "Dữ liệu giao dịch không hợp lệ.",
            "danger",
        )
    except psycopg2.IntegrityError:
        flash("Không thể lưu giao dịch do dữ liệu vi phạm ràng buộc.", "danger")
    return redirect(url_for("index"))


@app.get("/api/products")
def api_list_products():
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute("SELECT * FROM products ORDER BY id ASC")
            products = [_row_dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
    finally:
        conn.close()
    return jsonify(products)


@app.post("/api/products")
def api_create_product():
    data = _validate_product_fields(
        _json_body(),
        ("sku", "name", "quantity", "min_threshold"),
        ("sku", "name"),
    )
    data.setdefault("quantity", 0)
    data.setdefault("min_threshold", 5)

    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute(
                """
                INSERT INTO products (sku, name, quantity, min_threshold)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (data["sku"], data["name"], data["quantity"], data["min_threshold"]),
            )
            product = _row_dict(cur.fetchone())
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()
    return jsonify(product), 201


@app.route("/api/products/<int:product_id>", methods=["GET", "PUT", "PATCH", "DELETE"])
def api_product(product_id):
    if request.method == "GET":
        product = _get_product(product_id)
        if product is None:
            raise ApiError("Không tìm thấy sản phẩm.", 404)
        return jsonify(product)

    if request.method in ("PUT", "PATCH"):
        data = _validate_product_fields(
            _json_body(),
            ("sku", "name", "min_threshold"),
            ("sku", "name", "min_threshold") if request.method == "PUT" else (),
        )
        if not data:
            raise ApiError("Cần cung cấp ít nhất một trường để cập nhật.", 400)

        fields = list(data)
        assignments = ", ".join(f"{field} = %s" for field in fields)
        values = [data[field] for field in fields]
        conn = get_db_connection()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cur.execute(
                    f"""
                    UPDATE products
                    SET {assignments}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING *
                    """,
                    (*values, product_id),
                )
                product = _row_dict(cur.fetchone())
                if product is None:
                    raise ApiError("Không tìm thấy sản phẩm.", 404)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()
        finally:
            conn.close()
        return jsonify(product)

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM products WHERE id = %s RETURNING id", (product_id,))
            deleted = cur.fetchone()
            if deleted is None:
                raise ApiError("Không tìm thấy sản phẩm.", 404)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()
    return "", 204


@app.get("/api/transactions")
def api_list_transactions():
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute(
                """
                SELECT t.id, t.product_id, p.sku, p.name AS product_name,
                       t.type, t.quantity, t.created_at
                FROM transactions AS t
                JOIN products AS p ON p.id = t.product_id
                ORDER BY t.created_at DESC, t.id DESC
                """
            )
            transactions = [_row_dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
    finally:
        conn.close()
    return jsonify(transactions)


@app.post("/api/transactions")
def api_create_transaction():
    data = _json_body()
    if set(data) != {"product_id", "type", "quantity"}:
        raise ApiError("Cần gửi đúng các trường product_id, type và quantity.", 400)
    product_id = data["product_id"]
    if type(product_id) is not int or product_id <= 0:
        raise ApiError("'product_id' phải là số nguyên dương.", 400)

    product, transaction_record = _perform_stock_transaction(
        product_id, data["type"], data["quantity"]
    )
    return jsonify({"product": product, "transaction": transaction_record}), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
