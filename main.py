from fastmcp import FastMCP
import mysql.connector
from mysql.connector import Error
import os
import json

# --- MySQL Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "user": "expense_user",
    "password": "your_password",   # Replace with your actual password
    "database": "expense_tracker_db"
}

CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

# --- Initialize MCP Server ---
mcp = FastMCP("ExpenseTracker")

# --- Initialize Database ----
def init_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Expenses Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                amount FLOAT NOT NULL,
                category VARCHAR(255) NOT NULL,
                subcategory VARCHAR(255) DEFAULT '',
                note TEXT
            )
        """)

        # Income Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                amount FLOAT NOT NULL,
                source VARCHAR(255) NOT NULL,
                note TEXT
            )
        """)

        conn.commit()

    except Error as e:
        print(f"Error while connecting to MySQL: {e}")

    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

init_db()

# ==============================
# EXPENSE TOOLS
# ==============================

@mcp.tool()
def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    """Add a new expense entry. Date format: YYYY-MM-DD."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO expenses (date, amount, category, subcategory, note) VALUES (%s, %s, %s, %s, %s)",
            (date, amount, category, subcategory, note)
        )
        conn.commit()
        return {"status": "ok", "id": cursor.lastrowid}
    finally:
        cursor.close()
        conn.close()


@mcp.tool()
def edit_expense(expense_id: int, date: str = None, amount: float = None,
                 category: str = None, subcategory: str = None, note: str = None):
    """Edit an existing expense by ID."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        updates = []
        params = []

        if date:
            updates.append("date = %s")
            params.append(date)
        if amount:
            updates.append("amount = %s")
            params.append(amount)
        if category:
            updates.append("category = %s")
            params.append(category)
        if subcategory is not None:
            updates.append("subcategory = %s")
            params.append(subcategory)
        if note is not None:
            updates.append("note = %s")
            params.append(note)

        if not updates:
            return {"status": "error", "message": "No fields provided to update"}

        query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = %s"
        params.append(expense_id)

        cursor.execute(query, params)
        conn.commit()

        return {"status": "ok", "updated_id": expense_id}

    finally:
        cursor.close()
        conn.close()


@mcp.tool()
def delete_expense(expense_id: int):
    """Delete an expense by ID."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        conn.commit()
        return {"status": "ok", "deleted_id": expense_id}
    finally:
        cursor.close()
        conn.close()


@mcp.tool()
def list_expenses(start_date: str, end_date: str):
    """List all expenses between start_date and end_date (YYYY-MM-DD)."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, date, amount, category, subcategory, note "
            "FROM expenses WHERE date BETWEEN %s AND %s ORDER BY date ASC",
            (start_date, end_date)
        )
        rows = cursor.fetchall()
        for row in rows:
            row["date"] = str(row["date"])
        return rows
    finally:
        cursor.close()
        conn.close()


@mcp.tool()
def summarize_expenses(start_date: str, end_date: str):
    """Summarize expenses by category."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT category, SUM(amount) AS total_amount "
            "FROM expenses WHERE date BETWEEN %s AND %s "
            "GROUP BY category ORDER BY total_amount DESC",
            (start_date, end_date)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ==============================
# INCOME TOOLS
# ==============================

@mcp.tool()
def add_income(date: str, amount: float, source: str, note: str = ""):
    """Add income (salary, freelance, etc)."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO income (date, amount, source, note) VALUES (%s, %s, %s, %s)",
            (date, amount, source, note)
        )
        conn.commit()
        return {"status": "ok", "id": cursor.lastrowid}
    finally:
        cursor.close()
        conn.close()


@mcp.tool()
def list_income(start_date: str, end_date: str):
    """List income between dates."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, date, amount, source, note "
            "FROM income WHERE date BETWEEN %s AND %s ORDER BY date ASC",
            (start_date, end_date)
        )
        rows = cursor.fetchall()
        for row in rows:
            row["date"] = str(row["date"])
        return rows
    finally:
        cursor.close()
        conn.close()


# ==============================
# NET SUMMARY
# ==============================

@mcp.tool()
def net_summary(start_date: str, end_date: str):
    """Calculate total income, total expense, and net balance."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT IFNULL(SUM(amount),0) FROM income WHERE date BETWEEN %s AND %s",
            (start_date, end_date)
        )
        total_income = cursor.fetchone()[0]

        cursor.execute(
            "SELECT IFNULL(SUM(amount),0) FROM expenses WHERE date BETWEEN %s AND %s",
            (start_date, end_date)
        )
        total_expense = cursor.fetchone()[0]

        return {
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "net_balance": float(total_income - total_expense)
        }

    finally:
        cursor.close()
        conn.close()


# --- Categories Resource ---
@mcp.resource("expense://categories")
def get_categories() -> str:
    """Load categories from JSON file."""
    if not os.path.exists(CATEGORIES_PATH):
        return json.dumps({"categories": ["Food", "Transport", "Rent", "Other"]})

    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()


# --- Start the Server ---

if __name__ == "__main__":
    mcp.run(transport='http',host='0.0.0.0',port=8000)
