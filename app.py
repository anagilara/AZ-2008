from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "payments.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-in-production"


STATUS_OPTIONS = ["pending", "paid", "overdue", "cancelled"]
METHOD_OPTIONS = ["bank-transfer", "credit-card", "debit-card", "cash", "other"]
TYPE_OPTIONS = ["service", "subscription", "tax", "rent", "salary", "other"]


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payer TEXT NOT NULL,
                concept TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0),
                due_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                method TEXT NOT NULL DEFAULT 'other',
                payment_type TEXT NOT NULL DEFAULT 'other',
                notes TEXT,
                paid_date TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def migrate_db() -> None:
    with get_db_connection() as conn:
        columns = conn.execute("PRAGMA table_info(payments)").fetchall()
        existing_columns = {column[1] for column in columns}
        if "payment_type" not in existing_columns:
            conn.execute(
                "ALTER TABLE payments ADD COLUMN payment_type TEXT NOT NULL DEFAULT 'other'"
            )


def refresh_overdue_statuses() -> None:
    today = date.today().isoformat()
    with get_db_connection() as conn:
        conn.execute(
            """
            UPDATE payments
            SET status = 'overdue'
            WHERE status = 'pending'
            AND due_date < ?
            """,
            (today,),
        )


def parse_amount(raw_amount: str) -> float | None:
    try:
        amount = float(raw_amount)
    except ValueError:
        return None

    if amount < 0:
        return None
    return amount


@app.route("/")
def index():
    refresh_overdue_statuses()

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "all").strip()

    query = "SELECT * FROM payments WHERE 1=1"
    params: list[str] = []

    if q:
        query += " AND (payer LIKE ? OR concept LIKE ? OR notes LIKE ? OR payment_type LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term, term])

    if status != "all":
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY due_date ASC, created_at DESC"

    with get_db_connection() as conn:
        payments = conn.execute(query, params).fetchall()

        summary = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END), 0) as total_paid,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END), 0) as total_pending,
                COALESCE(SUM(CASE WHEN status = 'overdue' THEN amount ELSE 0 END), 0) as total_overdue
            FROM payments
            """
        ).fetchone()

    return render_template(
        "index.html",
        payments=payments,
        summary=summary,
        q=q,
        status=status,
        status_options=STATUS_OPTIONS,
    )


@app.route("/payments/new", methods=["GET", "POST"])
def create_payment():
    if request.method == "POST":
        payer = request.form.get("payer", "").strip()
        concept = request.form.get("concept", "").strip()
        amount = parse_amount(request.form.get("amount", ""))
        due_date = request.form.get("due_date", "").strip()
        status = request.form.get("status", "pending").strip()
        method = request.form.get("method", "other").strip()
        payment_type = request.form.get("payment_type", "other").strip()
        notes = request.form.get("notes", "").strip()

        if not payer or not concept or not due_date or amount is None:
            flash("Completa los campos obligatorios con datos validos.", "error")
            return render_template(
                "payment_form.html",
                payment=request.form,
                mode="create",
                status_options=STATUS_OPTIONS,
                method_options=METHOD_OPTIONS,
            )

        if status not in STATUS_OPTIONS:
            status = "pending"
        if method not in METHOD_OPTIONS:
            method = "other"
        if payment_type not in TYPE_OPTIONS:
            payment_type = "other"

        paid_date = date.today().isoformat() if status == "paid" else None

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO payments
                (payer, concept, amount, due_date, status, method, payment_type, notes, paid_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payer,
                    concept,
                    amount,
                    due_date,
                    status,
                    method,
                    payment_type,
                    notes,
                    paid_date,
                    datetime.utcnow().isoformat(timespec="seconds"),
                ),
            )

        flash("Pago creado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template(
        "payment_form.html",
        payment={},
        mode="create",
        status_options=STATUS_OPTIONS,
        method_options=METHOD_OPTIONS,
        type_options=TYPE_OPTIONS,
    )


@app.route("/payments/<int:payment_id>/edit", methods=["GET", "POST"])
def edit_payment(payment_id: int):
    with get_db_connection() as conn:
        payment = conn.execute(
            "SELECT * FROM payments WHERE id = ?", (payment_id,)
        ).fetchone()

    if payment is None:
        flash("El pago no existe.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        payer = request.form.get("payer", "").strip()
        concept = request.form.get("concept", "").strip()
        amount = parse_amount(request.form.get("amount", ""))
        due_date = request.form.get("due_date", "").strip()
        status = request.form.get("status", "pending").strip()
        method = request.form.get("method", "other").strip()
        payment_type = request.form.get("payment_type", "other").strip()
        notes = request.form.get("notes", "").strip()

        if not payer or not concept or not due_date or amount is None:
            flash("Completa los campos obligatorios con datos validos.", "error")
            return render_template(
                "payment_form.html",
                payment=request.form,
                mode="edit",
                payment_id=payment_id,
                status_options=STATUS_OPTIONS,
                method_options=METHOD_OPTIONS,
                type_options=TYPE_OPTIONS,
            )

        if status not in STATUS_OPTIONS:
            status = "pending"
        if method not in METHOD_OPTIONS:
            method = "other"
        if payment_type not in TYPE_OPTIONS:
            payment_type = "other"

        paid_date = date.today().isoformat() if status == "paid" else None

        with get_db_connection() as conn:
            conn.execute(
                """
                UPDATE payments
                SET payer = ?, concept = ?, amount = ?, due_date = ?,
                    status = ?, method = ?, payment_type = ?, notes = ?, paid_date = ?
                WHERE id = ?
                """,
                (
                    payer,
                    concept,
                    amount,
                    due_date,
                    status,
                    method,
                    payment_type,
                    notes,
                    paid_date,
                    payment_id,
                ),
            )

        flash("Pago actualizado correctamente.", "success")
        return redirect(url_for("index"))

    return render_template(
        "payment_form.html",
        payment=payment,
        mode="edit",
        payment_id=payment_id,
        status_options=STATUS_OPTIONS,
        method_options=METHOD_OPTIONS,
        type_options=TYPE_OPTIONS,
    )


@app.route("/payments/<int:payment_id>/mark-paid", methods=["POST"])
def mark_paid(payment_id: int):
    with get_db_connection() as conn:
        conn.execute(
            """
            UPDATE payments
            SET status = 'paid', paid_date = ?
            WHERE id = ?
            """,
            (date.today().isoformat(), payment_id),
        )

    flash("Pago marcado como pagado.", "success")
    return redirect(url_for("index"))


@app.route("/payments/<int:payment_id>/delete", methods=["POST"])
def delete_payment(payment_id: int):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))

    flash("Pago eliminado.", "success")
    return redirect(url_for("index"))


init_db()
migrate_db()


if __name__ == "__main__":
    app.run(debug=True)
