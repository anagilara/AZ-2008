import sqlite3

import app as app_module


def _fetch_one_product():
    with sqlite3.connect(app_module.DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM products LIMIT 1").fetchone()


def _insert_product(name="Mouse", sku="MOU-001", category="electronica", price=20.5, stock=7):
    with sqlite3.connect(app_module.DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO products (name, sku, category, price, stock, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (name, sku, category, price, stock, "test product"),
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def test_create_product_success(client):
    response = client.post(
        "/products/new",
        data={
            "name": "Teclado Mecanico",
            "sku": "tec-100",
            "category": "electronica",
            "price": "89.99",
            "stock": "12",
            "description": "Switch blue",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Producto creado correctamente" in response.data

    created = _fetch_one_product()
    assert created is not None
    assert created["name"] == "Teclado Mecanico"
    assert created["sku"] == "TEC-100"


def test_index_lists_existing_product(client):
    _insert_product(name="Monitor", sku="MON-200")

    response = client.get("/")

    assert response.status_code == 200
    assert b"Monitor" in response.data
    assert b"MON-200" in response.data


def test_edit_product_success(client):
    product_id = _insert_product(name="Laptop", sku="LAP-001", stock=5)

    response = client.post(
        f"/products/{product_id}/edit",
        data={
            "name": "Laptop Pro",
            "sku": "LAP-001",
            "category": "electronica",
            "price": "1499.00",
            "stock": "8",
            "description": "Edicion 2026",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Producto actualizado correctamente" in response.data

    updated = _fetch_one_product()
    assert updated is not None
    assert updated["name"] == "Laptop Pro"
    assert float(updated["price"]) == 1499.0
    assert int(updated["stock"]) == 8


def test_delete_product_success(client):
    product_id = _insert_product(name="Auriculares", sku="AUR-900")

    response = client.post(f"/products/{product_id}/delete", follow_redirects=True)

    assert response.status_code == 200
    assert b"Producto eliminado" in response.data

    with sqlite3.connect(app_module.DB_PATH) as conn:
        remaining = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    assert remaining == 0
