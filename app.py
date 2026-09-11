from flask import Flask, request, redirect, session, render_template_string, flash
import sqlite3
import re
from datetime import datetime
from difflib import SequenceMatcher

app = Flask(__name__)
app.secret_key = "expense-claims-secret"

DB = "expense_claims.db"


# ================= DATABASE =================

def db():
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    return connection


def setup_database():
    connection = db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            monthly_limit REAL NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            merchant TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            expense_date TEXT NOT NULL,
            description TEXT,
            receipt_text TEXT,
            status TEXT NOT NULL DEFAULT 'Submitted',
            created_at TEXT NOT NULL,
            approved_by INTEGER,
            paid_at TEXT
        )
    """)

    users = [
        ("Ananya Rao", "staff@demo.com", "1234", "Staff", 10000),
        ("Rahul Kumar", "manager@demo.com", "1234", "Manager", 15000),
        ("Priya Sharma", "finance@demo.com", "1234", "Finance", 25000),
        ("Arjun Reddy", "arjun@demo.com", "1234", "Staff", 8000)
    ]

    for user in users:
        try:
            connection.execute("""
                INSERT INTO users
                (name, email, password, role, monthly_limit)
                VALUES (?, ?, ?, ?, ?)
            """, user)
        except sqlite3.IntegrityError:
            pass

    connection.commit()
    connection.close()


# ================= RECEIPT EXTRACTION =================

def extract_receipt(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    merchant = lines[0] if lines else ""

    amount = 0

    match = re.search(
        r"(?:total|amount|paid|price)"
        r"\s*[:\-]?\s*[₹Rs.\s]*"
        r"([0-9]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE
    )

    if match:
        amount = float(match.group(1))
    else:
        numbers = re.findall(
            r"\b[0-9]+(?:\.[0-9]+)?\b",
            text
        )
        if numbers:
            amount = float(numbers[-1])

    expense_date = datetime.now().strftime("%Y-%m-%d")

    date_match = re.search(
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",
        text
    )

    if date_match:
        day, month, year = date_match.groups()

        if len(year) == 2:
            year = "20" + year

        try:
            expense_date = datetime(
                int(year),
                int(month),
                int(day)
            ).strftime("%Y-%m-%d")
        except ValueError:
            pass

    text_lower = text.lower()

    if any(x in text_lower for x in
           ["uber", "ola", "taxi", "cab", "auto", "metro", "bus"]):
        category = "Travel"

    elif any(x in text_lower for x in
             ["restaurant", "cafe", "food", "meal", "coffee", "biryani"]):
        category = "Meals"

    elif any(x in text_lower for x in
             ["hotel", "room", "stay"]):
        category = "Accommodation"

    elif any(x in text_lower for x in
             ["stationery", "paper", "pen", "office"]):
        category = "Supplies"

    else:
        category = "Other"

    return {
        "merchant": merchant,
        "amount": amount,
        "date": expense_date,
        "category": category
    }


# ================= DUPLICATE CHECK =================

def clean(value):
    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


def duplicate_receipt(merchant, amount, date, receipt_text):

    connection = db()

    claims = connection.execute("""
        SELECT merchant, amount, expense_date, receipt_text
        FROM claims
        WHERE amount = ?
    """, (amount,)).fetchall()

    connection.close()

    current = clean(
        merchant + str(amount) + date + receipt_text
    )

    for claim in claims:

        old = clean(
            claim["merchant"]
            + str(claim["amount"])
            + claim["expense_date"]
            + claim["receipt_text"]
        )

        similarity = SequenceMatcher(
            None,
            current,
            old
        ).ratio()

        same_details = (
            clean(merchant) == clean(claim["merchant"])
            and float(amount) == float(claim["amount"])
            and date == claim["expense_date"]
        )

        if similarity >= 0.70 or same_details:
            return True

    return False


# ================= MONTHLY SPEND =================

def monthly_spend(user_id):

    month = datetime.now().strftime("%Y-%m")

    connection = db()

    result = connection.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM claims
        WHERE user_id = ?
        AND substr(expense_date, 1, 7) = ?
        AND status != 'Rejected'
    """, (user_id, month)).fetchone()

    connection.close()

    return float(result["total"])


# ================= STYLE =================

STYLE = """
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f7fa;
    color: #202124;
}

.nav {
    background: #1f2937;
    color: white;
    padding: 16px 28px;
    display: flex;
    justify-content: space-between;
}

.nav a {
    color: white;
    text-decoration: none;
    margin-left: 15px;
}

.container {
    max-width: 1100px;
    margin: 30px auto;
    padding: 0 20px;
}

.card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,.06);
}

.cards {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(220px, 1fr));
    gap: 18px;
}

.stat {
    background: white;
    padding: 20px;
    border-radius: 12px;
}

input, select, textarea {
    width: 100%;
    padding: 11px;
    border: 1px solid #d1d5db;
    border-radius: 7px;
    margin: 7px 0 15px;
}

textarea { min-height: 140px; }

button, .btn {
    display: inline-block;
    border: 0;
    padding: 10px 16px;
    border-radius: 7px;
    background: #2563eb;
    color: white;
    text-decoration: none;
    cursor: pointer;
}

.green { background: #16a34a; }
.red { background: #dc2626; }
.orange { background: #d97706; }

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
}

.badge {
    background: #e5e7eb;
    padding: 5px 9px;
    border-radius: 20px;
}

.alert {
    background: #fff3cd;
    padding: 12px;
    border-radius: 7px;
    margin-bottom: 15px;
}

.muted { color: #6b7280; }

.login {
    max-width: 420px;
    margin: 80px auto;
}

.progress {
    height: 8px;
    background: #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: #2563eb;
}
</style>
"""


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        connection = db()

        user = connection.execute("""
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
        """, (email, password)).fetchone()

        connection.close()

        if user:
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            return redirect("/")

        flash("Email or password is incorrect.")

    return render_template_string(
        STYLE + """
        <div class="login card">

            <h1>Expense Claims</h1>

            <p class="muted">
                Sign in to manage your expenses.
            </p>

            {% for message in get_flashed_messages() %}
                <div class="alert">{{ message }}</div>
            {% endfor %}

            <form method="POST">

                <label>Email</label>

                <input
                    type="email"
                    name="email"
                    placeholder="Enter email"
                    required
                >

                <label>Password</label>

                <input
                    type="password"
                    name="password"
                    placeholder="Enter password"
                    required
                >

                <button>Sign in</button>

            </form>

            <hr>

            <small>
                <b>Demo accounts</b><br><br>

                Staff:
                staff@demo.com / 1234<br>

                Manager:
                manager@demo.com / 1234<br>

                Finance:
                finance@demo.com / 1234
            </small>

        </div>
        """
    )


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/login")


# ================= DASHBOARD =================

@app.route("/")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    role = session["role"]

    connection = db()

    # STAFF
    if role == "Staff":

        user = connection.execute("""
            SELECT *
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        claims = connection.execute("""
            SELECT *
            FROM claims
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

        connection.close()

        spent = monthly_spend(user_id)
        remaining = max(
            user["monthly_limit"] - spent,
            0
        )

        percentage = 0

        if user["monthly_limit"] > 0:
            percentage = min(
                int(spent / user["monthly_limit"] * 100),
                100
            )

        return render_template_string(
            STYLE + """
            <div class="nav">
                <b>Expense Claims</b>

                <div>
                    {{ session["name"] }}
                    <a href="/logout">Logout</a>
                </div>
            </div>

            <div class="container">

                <h1>My Expenses</h1>

                <div class="cards">

                    <div class="stat">
                        <div class="muted">
                            Spent this month
                        </div>
                        <h2>
                            ₹{{ "%.2f"|format(spent) }}
                        </h2>
                    </div>

                    <div class="stat">
                        <div class="muted">
                            Monthly limit
                        </div>
                        <h2>
                            ₹{{ "%.2f"|format(
                                user["monthly_limit"]
                            ) }}
                        </h2>
                    </div>

                    <div class="stat">
                        <div class="muted">
                            Remaining
                        </div>
                        <h2>
                            ₹{{ "%.2f"|format(remaining) }}
                        </h2>
                    </div>

                </div>

                <div class="card">

                    <div class="progress">
                        <div
                            class="progress-bar"
                            style="width: {{ percentage }}%"
                        ></div>
                    </div>

                    <p class="muted">
                        {{ percentage }}% of monthly limit used
                    </p>

                    <a class="btn" href="/claim/new">
                        + New claim
                    </a>

                </div>

                <div class="card">

                    <h2>My claims</h2>

                    <table>

                        <tr>
                            <th>Merchant</th>
                            <th>Amount</th>
                            <th>Category</th>
                            <th>Date</th>
                            <th>Status</th>
                        </tr>

                        {% for claim in claims %}

                        <tr>
                            <td>{{ claim["merchant"] }}</td>
                            <td>
                                ₹{{ "%.2f"|format(
                                    claim["amount"]
                                ) }}
                            </td>
                            <td>{{ claim["category"] }}</td>
                            <td>{{ claim["expense_date"] }}</td>
                            <td>
                                <span class="badge">
                                    {{ claim["status"] }}
                                </span>
                            </td>
                        </tr>

                        {% else %}

                        <tr>
                            <td colspan="5">
                                No claims submitted yet.
                            </td>
                        </tr>

                        {% endfor %}

                    </table>

                </div>

            </div>
            """,
            user=user,
            claims=claims,
            spent=spent,
            remaining=remaining,
            percentage=percentage
        )


    # MANAGER
    if role == "Manager":

        pending = connection.execute("""
            SELECT
                claims.*,
                users.name AS employee
            FROM claims
            JOIN users
                ON claims.user_id = users.id
            WHERE claims.status = 'Submitted'
            AND claims.user_id != ?
            ORDER BY claims.id DESC
        """, (user_id,)).fetchall()

        my_claims = connection.execute("""
            SELECT *
            FROM claims
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

        connection.close()

        return render_template_string(
            STYLE + """
            <div class="nav">
                <b>Expense Claims</b>

                <div>
                    {{ session["name"] }}
                    <a href="/logout">Logout</a>
                </div>
            </div>

            <div class="container">

                <h1>Manager Review</h1>

                <div class="card">

                    <p class="muted">
                        Review team claims. Your own claims
                        cannot be approved by you.
                    </p>

                    <table>

                        <tr>
                            <th>Employee</th>
                            <th>Merchant</th>
                            <th>Amount</th>
                            <th>Category</th>
                            <th>Action</th>
                        </tr>

                        {% for claim in pending %}

                        <tr>

                            <td>{{ claim["employee"] }}</td>

                            <td>{{ claim["merchant"] }}</td>

                            <td>
                                ₹{{ "%.2f"|format(
                                    claim["amount"]
                                ) }}
                            </td>

                            <td>{{ claim["category"] }}</td>

                            <td>

                                <a
                                    class="btn green"
                                    href="/approve/{{ claim["id"] }}"
                                >
                                    Approve
                                </a>

                                <a
                                    class="btn red"
                                    href="/reject/{{ claim["id"] }}"
                                >
                                    Reject
                                </a>

                            </td>

                        </tr>

                        {% else %}

                        <tr>
                            <td colspan="5">
                                No claims waiting for review.
                            </td>
                        </tr>

                        {% endfor %}

                    </table>

                </div>

                <div class="card">

                    <h2>My claims</h2>

                    <a
                        class="btn"
                        href="/claim/new"
                    >
                        + New personal claim
                    </a>

                    <br><br>

                    <table>

                        <tr>
                            <th>Merchant</th>
                            <th>Amount</th>
                            <th>Status</th>
                        </tr>

                        {% for claim in my_claims %}

                        <tr>
                            <td>{{ claim["merchant"] }}</td>
                            <td>
                                ₹{{ "%.2f"|format(
                                    claim["amount"]
                                ) }}
                            </td>
                            <td>{{ claim["status"] }}</td>
                        </tr>

                        {% else %}

                        <tr>
                            <td colspan="3">
                                No personal claims yet.
                            </td>
                        </tr>

                        {% endfor %}

                    </table>

                </div>

            </div>
            """,
            pending=pending,
            my_claims=my_claims
        )


    # FINANCE
    claims = connection.execute("""
        SELECT
            claims.*,
            users.name AS employee
        FROM claims
        JOIN users
            ON claims.user_id = users.id
        ORDER BY claims.id DESC
    """).fetchall()

    category_totals = connection.execute("""
        SELECT category, SUM(amount) AS total
        FROM claims
        WHERE status != 'Rejected'
        GROUP BY category
        ORDER BY total DESC
    """).fetchall()

    employee_totals = connection.execute("""
        SELECT
            users.name,
            users.monthly_limit,
            COALESCE(SUM(
                CASE
                    WHEN claims.status != 'Rejected'
                    THEN claims.amount
                    ELSE 0
                END
            ), 0) AS spent
        FROM users
        LEFT JOIN claims
            ON users.id = claims.user_id
        WHERE users.role != 'Finance'
        GROUP BY users.id
    """).fetchall()

    connection.close()

    return render_template_string(
        STYLE + """
        <div class="nav">

            <b>Expense Claims</b>

            <div>
                {{ session["name"] }}
                <a href="/logout">Logout</a>
            </div>

        </div>

        <div class="container">

            <h1>Finance Dashboard</h1>

            <div class="card">

                <h2>Spend by category</h2>

                <table>

                    <tr>
                        <th>Category</th>
                        <th>Total</th>
                    </tr>

                    {% for item in category_totals %}

                    <tr>
                        <td>{{ item["category"] }}</td>
                        <td>
                            ₹{{ "%.2f"|format(
                                item["total"]
                            ) }}
                        </td>
                    </tr>

                    {% else %}

                    <tr>
                        <td colspan="2">
                            No spending yet.
                        </td>
                    </tr>

                    {% endfor %}

                </table>

            </div>

            <div class="card">

                <h2>Monthly limits</h2>

                <table>

                    <tr>
                        <th>Employee</th>
                        <th>Spent</th>
                        <th>Limit</th>
                        <th>Status</th>
                    </tr>

                    {% for person in employee_totals %}

                    <tr>

                        <td>{{ person["name"] }}</td>

                        <td>
                            ₹{{ "%.2f"|format(
                                person["spent"]
                            ) }}
                        </td>

                        <td>
                            ₹{{ "%.2f"|format(
                                person["monthly_limit"]
                            ) }}
                        </td>

                        <td>

                            {% if person["spent"]
                                  >= person["monthly_limit"] %}

                                <span class="badge">
                                    Over limit
                                </span>

                            {% elif person["spent"]
                                  >= person["monthly_limit"] * 0.8 %}

                                <span class="badge">
                                    Near limit
                                </span>

                            {% else %}

                                <span class="badge">
                                    Within limit
                                </span>

                            {% endif %}

                        </td>

                    </tr>

                    {% endfor %}

                </table>

            </div>

            <div class="card">

                <h2>All claims</h2>

                <table>

                    <tr>
                        <th>Employee</th>
                        <th>Merchant</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>

                    {% for claim in claims %}

                    <tr>

                        <td>{{ claim["employee"] }}</td>
                        <td>{{ claim["merchant"] }}</td>

                        <td>
                            ₹{{ "%.2f"|format(
                                claim["amount"]
                            ) }}
                        </td>

                        <td>
                            <span class="badge">
                                {{ claim["status"] }}
                            </span>
                        </td>

                        <td>

                            {% if claim["status"] == "Approved" %}

                                <a
                                    class="btn green"
                                    href="/pay/{{ claim["id"] }}"
                                >
                                    Mark paid
                                </a>

                            {% elif claim["status"] == "Paid" %}

                                Completed

                            {% elif claim["status"] == "Rejected" %}

                                Rejected

                            {% else %}

                                Waiting

                            {% endif %}

                        </td>

                    </tr>

                    {% endfor %}

                </table>

            </div>

        </div>
        """,
        claims=claims,
        category_totals=category_totals,
        employee_totals=employee_totals
    )


# ================= NEW CLAIM =================

@app.route("/claim/new", methods=["GET", "POST"])
def new_claim():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] not in ["Staff", "Manager"]:
        return redirect("/")

    values = {
        "merchant": "",
        "amount": "",
        "category": "Other",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "receipt": "",
        "description": ""
    }

    # Extract details first
    if (
        request.method == "POST"
        and request.form.get("action") == "extract"
    ):

        receipt = request.form.get(
            "receipt",
            ""
        ).strip()

        extracted = extract_receipt(receipt)

        values = {
            "merchant": extracted["merchant"],
            "amount": extracted["amount"],
            "category": extracted["category"],
            "date": extracted["date"],
            "receipt": receipt,
            "description": ""
        }

        return render_template_string(
            STYLE + CLAIM_PAGE,
            values=values,
            extracted=True
        )

    # Submit after review
    if request.method == "POST":

        merchant = request.form.get(
            "merchant",
            ""
        ).strip()

        receipt = request.form.get(
            "receipt",
            ""
        ).strip()

        category = request.form.get(
            "category",
            "Other"
        )

        date = request.form.get(
            "date",
            ""
        )

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:
            amount = float(
                request.form.get("amount", "0")
            )
        except ValueError:
            amount = 0

        if not merchant or amount <= 0:

            flash(
                "Please check the merchant and amount."
            )

            values = {
                "merchant": merchant,
                "amount": amount,
                "category": category,
                "date": date,
                "receipt": receipt,
                "description": description
            }

            return render_template_string(
                STYLE + CLAIM_PAGE,
                values=values,
                extracted=True
            )

        if duplicate_receipt(
            merchant,
            amount,
            date,
            receipt
        ):

            flash(
                "This receipt looks like an existing claim."
            )

            values = {
                "merchant": merchant,
                "amount": amount,
                "category": category,
                "date": date,
                "receipt": receipt,
                "description": description
            }

            return render_template_string(
                STYLE + CLAIM_PAGE,
                values=values,
                extracted=True
            )

        connection = db()

        connection.execute("""
            INSERT INTO claims
            (
                user_id,
                merchant,
                amount,
                category,
                expense_date,
                description,
                receipt_text,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Submitted', ?)
        """, (
            session["user_id"],
            merchant,
            amount,
            category,
            date,
            description,
            receipt,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        connection.commit()
        connection.close()

        flash(
            "Claim submitted for manager review."
        )

        return redirect("/")

    return render_template_string(
        STYLE + CLAIM_PAGE,
        values=values,
        extracted=False
    )


CLAIM_PAGE = """

<div class="nav">

    <b>Expense Claims</b>

    <a href="/logout">Logout</a>

</div>

<div class="container">

    <div class="card">

        <h1>New expense claim</h1>

        <p class="muted">
            Paste your receipt text and extract the details.
            Review them before submitting.
        </p>

        {% for message in get_flashed_messages() %}
            <div class="alert">
                {{ message }}
            </div>
        {% endfor %}

        <form method="POST">

            <label>Receipt text</label>

            <textarea
                name="receipt"
                placeholder="Example:

Sri Lakshmi Cafe
Date: 18/09/2026
Meal
Total: ₹450"
                required
            >{{ values.receipt }}</textarea>

            <button
                type="submit"
                name="action"
                value="extract"
            >
                Extract details
            </button>

            {% if extracted %}

            <hr>

            <h3>Review extracted details</h3>

            <label>Merchant</label>

            <input
                name="merchant"
                value="{{ values.merchant }}"
                required
            >

            <label>Amount</label>

            <input
                type="number"
                step="0.01"
                name="amount"
                value="{{ values.amount }}"
                required
            >

            <label>Category</label>

            <select name="category">

                {% for category in [
                    "Travel",
                    "Meals",
                    "Accommodation",
                    "Supplies",
                    "Other"
                ] %}

                <option
                    value="{{ category }}"
                    {% if values.category == category %}
                    selected
                    {% endif %}
                >
                    {{ category }}
                </option>

                {% endfor %}

            </select>

            <label>Expense date</label>

            <input
                type="date"
                name="date"
                value="{{ values.date }}"
                required
            >

            <label>Description</label>

            <input
                name="description"
                value="{{ values.description }}"
                placeholder="Short description"
            >

            <br><br>

            <button
                type="submit"
                name="action"
                value="submit"
            >
                Submit claim
            </button>

            {% endif %}

            <a class="btn orange" href="/">
                Cancel
            </a>

        </form>

    </div>

</div>

"""


# ================= APPROVE =================

@app.route("/approve/<int:claim_id>")
def approve(claim_id):

    if session.get("role") != "Manager":
        return redirect("/")

    connection = db()

    claim = connection.execute("""
        SELECT *
        FROM claims
        WHERE id = ?
    """, (claim_id,)).fetchone()

    if claim:

        if claim["user_id"] == session["user_id"]:

            flash(
                "You cannot approve your own claim."
            )

        elif claim["status"] == "Submitted":

            connection.execute("""
                UPDATE claims
                SET status = 'Approved',
                    approved_by = ?
                WHERE id = ?
                AND status = 'Submitted'
            """, (
                session["user_id"],
                claim_id
            ))

            connection.commit()

    connection.close()

    return redirect("/")


# ================= REJECT =================

@app.route("/reject/<int:claim_id>")
def reject(claim_id):

    if session.get("role") != "Manager":
        return redirect("/")

    connection = db()

    claim = connection.execute("""
        SELECT *
        FROM claims
        WHERE id = ?
    """, (claim_id,)).fetchone()

    if claim:

        if claim["user_id"] == session["user_id"]:

            flash(
                "You cannot reject your own claim."
            )

        elif claim["status"] == "Submitted":

            connection.execute("""
                UPDATE claims
                SET status = 'Rejected',
                    approved_by = ?
                WHERE id = ?
                AND status = 'Submitted'
            """, (
                session["user_id"],
                claim_id
            ))

            connection.commit()

    connection.close()

    return redirect("/")


# ================= PAYMENT =================

@app.route("/pay/<int:claim_id>")
def pay(claim_id):

    if session.get("role") != "Finance":
        return redirect("/")

    connection = db()

    connection.execute("""
        UPDATE claims
        SET status = 'Paid',
            paid_at = ?
        WHERE id = ?
        AND status = 'Approved'
    """, (
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        claim_id
    ))

    connection.commit()
    connection.close()

    return redirect("/")


# ================= START =================

if __name__ == "__main__":

    setup_database()

    app.run(debug=True)