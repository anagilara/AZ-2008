from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "products.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-in-production"
app.config["_db_initialized"] = False

CATEGORY_OPTIONS = [
    "electronica",
    "hogar",
    "ropa",
    "deportes",
    "belleza",
    "alimentos",
    "otros",
]


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT 'otros',
                price REAL NOT NULL CHECK (price >= 0),
                stock INTEGER NOT NULL CHECK (stock >= 0),
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def migrate_db() -> None:
    with get_db_connection() as conn:
        columns = conn.execute("PRAGMA table_info(products)").fetchall()
        existing_columns = {column[1] for column in columns}
        if "updated_at" not in existing_columns:
            conn.execute(
                "ALTER TABLE products ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"
            )


def setup_database() -> None:
    init_db()
    migrate_db()


@app.before_request
def ensure_database_ready() -> None:
    if app.config.get("_db_initialized"):
        return
    setup_database()
    app.config["_db_initialized"] = True


def parse_price(raw_price: str) -> float | None:
    try:
        price = float(raw_price)
    except ValueError:
        return None

    if price < 0:
        return None
    return price


def parse_stock(raw_stock: str) -> int | None:
    try:
        stock = int(raw_stock)
    except ValueError:
        return None

    if stock < 0:
        return None
    return stock


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "all").strip()

    query = "SELECT * FROM products WHERE 1=1"
    params: list[str] = []

    if q:
        query += " AND (name LIKE ? OR sku LIKE ? OR category LIKE ? OR description LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term, term])

    if category != "all":
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY created_at DESC"

    with get_db_connection() as conn:
        products = conn.execute(query, params).fetchall()

        summary = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                COALESCE(SUM(stock), 0) as total_stock,
                COALESCE(SUM(price * stock), 0) as inventory_value,
                COALESCE(SUM(CASE WHEN stock <= 5 THEN 1 ELSE 0 END), 0) as low_stock
            FROM products
            """
        ).fetchone()

    return render_template(
        "index.html",
        products=products,
        summary=summary,
        q=q,
        category=category,
        category_options=CATEGORY_OPTIONS,
    )


@app.route("/products/new", methods=["GET", "POST"])
def create_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip().upper()
        category = request.form.get("category", "otros").strip()
        price = parse_price(request.form.get("price", ""))
        stock = parse_stock(request.form.get("stock", ""))
        description = request.form.get("description", "").strip()

        if not name or not sku or price is None or stock is None:
            flash("Completa los campos obligatorios con datos validos.", "error")
            return render_template(
                "payment_form.html",
                product=request.form,
                mode="create",
                category_options=CATEGORY_OPTIONS,
            )

        if category not in CATEGORY_OPTIONS:
            category = "otros"

        timestamp = datetime.utcnow().isoformat(timespec="seconds")

        with get_db_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO products
                    (name, sku, category, price, stock, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, sku, category, price, stock, description, timestamp, timestamp),
                )
            except sqlite3.IntegrityError:
                flash("El SKU ya existe. Usa un SKU unico.", "error")
                return render_template(
                    "payment_form.html",
                    product=request.form,
                    mode="create",
                    category_options=CATEGORY_OPTIONS,
                )

        flash("Producto creado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template(
        "payment_form.html",
        product={},
        mode="create",
        category_options=CATEGORY_OPTIONS,
    )


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id: int):
    with get_db_connection() as conn:
        product = conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()

    if product is None:
        flash("El producto no existe.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip().upper()
        category = request.form.get("category", "otros").strip()
        price = parse_price(request.form.get("price", ""))
        stock = parse_stock(request.form.get("stock", ""))
        description = request.form.get("description", "").strip()

        if not name or not sku or price is None or stock is None:
            flash("Completa los campos obligatorios con datos validos.", "error")
            return render_template(
                "payment_form.html",
                product=request.form,
                mode="edit",
                product_id=product_id,
                category_options=CATEGORY_OPTIONS,
            )

        if category not in CATEGORY_OPTIONS:
            category = "otros"

        with get_db_connection() as conn:
            try:
                conn.execute(
                    """
                    UPDATE products
                    SET name = ?, sku = ?, category = ?, price = ?, stock = ?, description = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        name,
                        sku,
                        category,
                        price,
                        stock,
                        description,
                        datetime.utcnow().isoformat(timespec="seconds"),
                        product_id,
                    ),
                )
            except sqlite3.IntegrityError:
                flash("El SKU ya existe. Usa un SKU unico.", "error")
                return render_template(
                    "payment_form.html",
                    product=request.form,
                    mode="edit",
                    product_id=product_id,
                    category_options=CATEGORY_OPTIONS,
                )

        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template(
        "payment_form.html",
        product=product,
        mode="edit",
        product_id=product_id,
        category_options=CATEGORY_OPTIONS,
    )


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id: int):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))

    flash("Producto eliminado.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    setup_database()
    app.config["_db_initialized"] = True
    app.run(debug=True)
