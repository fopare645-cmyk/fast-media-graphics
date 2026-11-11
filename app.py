Line 1: import sqlite3
Line 2: import os
Line 3: from flask import Flask, request, redirect, session, render_template_string
Line 4: from datetime import date

app = Flask(__name__)
app.secret_key = "fast-media-graphic-secret"
DB = "press.db"

# --- USERS ---
# Admin (Daddy) sees ALL money + can delete
# Worker sees NO money + CANNOT delete, only add orders + print
USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "Daddy (Admin)"},
    "worker": {"password": "worker123", "role": "worker", "name": "Worker"},
}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT, phone TEXT, job TEXT, size TEXT,
        qty INTEGER, price REAL, paid REAL, balance REAL, date TEXT, status TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT, amount REAL, date TEXT, note TEXT)""")
    conn.commit()
    conn.close()

init_db()

def is_admin():
    return session.get("role") == "admin"

# --- LOGIN ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u in USERS and USERS[u]["password"] == p:
            session["user"] = u
            session["role"] = USERS[u]["role"]
            session["name"] = USERS[u]["name"]
            return redirect("/dashboard")
        return "<h3>Wrong username or password. <a href='/'>Try again</a></h3>"
    return render_template_string("""
    <style>body{font-family:Arial;background:#0f172a;color:white;display:flex;justify-content:center;align-items:center;height:100vh;margin:0} .box{background:white;color:black;padding:30px;border-radius:15px;width:340px;text-align:center} .box img{width:130px} input{width:100%;padding:12px;margin:8px 0;border:1px solid #ccc;border-radius:8px;box-sizing:border-box} button{width:100%;padding:12px;background:#1e40af;color:white;border:none;border-radius:8px;font-weight:bold;cursor:pointer}</style>
    <div class='box'><img src='/static/logo.png'><h2 style='margin:5px 0'>Fast Media Graphic</h2><p style='margin:0;color:#666'>Bardnersville, Patience Shop<br>Monrovia, Liberia<br>0770008720 / 0880450579 / 0776573725</p><br>
    <form method='post'><input name='username' placeholder='Username - admin or worker' required>
    <input type='password' name='password' placeholder='Password' required>
    <button>LOGIN</button></form>
    <p style='font-size:12px;color:#666'>Admin: admin / admin123<br>Worker: worker / worker123</p>
    <p style='font-size:11px;color:#2f6fd1;font-weight:bold'>We serve with professionalism</p></div>
    """)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# --- DASHBOARD ---
@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect("/")
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    expenses = conn.execute("SELECT * FROM expenses ORDER BY id DESC").fetchall()
    today = str(date.today())
    today_orders = [o for o in orders if o["date"] == today]
    total_sales = sum(o["price"] for o in orders)
    today_sales = sum(o["price"] for o in today_orders)
    total_owed = sum(o["balance"] for o in orders)
    total_exp = sum(e["amount"] for e in expenses)
    total_paid = sum(o["paid"] for o in orders)
    conn.close()
    admin = is_admin()
    money_html = f"""
    <div style='display:flex;gap:10px;flex-wrap:wrap'>
      <div class='card'><h3>Total Sales</h3><b>${total_sales:.2f}</b></div>
      <div class='card'><h3>Today Sales</h3><b>${today_sales:.2f}</b></div>
      <div class='card'><h3>Money Owed by Customers</h3><b style='color:red'>${total_owed:.2f}</b></div>
      <div class='card'><h3>Expenses</h3><b>${total_exp:.2f}</b></div>
      <div class='card'><h3>Money In Hand</h3><b style='color:green'>${total_paid - total_exp:.2f}</b></div>
    </div>""" if admin else "<p style='background:#fef9c3;padding:15px;border-radius:10px'>👋 Welcome Worker! You can add orders and print receipts. Total money is hidden for workers.</p>"
    rows = ""
    for o in orders:
        del_btn = f"<a href='/delete_order/{o['id']}' onclick=\"return confirm('Delete?')\" style='color:red'>Delete</a>" if admin else "-"
        rows += f"<tr><td>{o['id']}</td><td>{o['customer']}</td><td>{o['job']} {o['size']}</td><td>{o['qty']}</td><td>${o['price']:.2f}</td><td>${o['paid']:.2f}</td><td>${o['balance']:.2f}</td><td>{o['date']}</td><td><a href='/receipt/{o['id']}' target='_blank'>Print Receipt</a> | {del_btn}</td></tr>"
    exp_rows = "".join([f"<tr><td>{e['item']}</td><td>${e['amount']:.2f}</td><td>{e['date']}</td><td>{e['note']}</td></tr>" for e in expenses]) if admin else "<tr><td colspan='4'>Hidden for workers</td></tr>"
    return render_template_string("""
    <style>body{font-family:Arial;background:#f1f5f9;padding:20px} .card{background:white;padding:15px;border-radius:10px;box-shadow:0 2px 5px #ccc;min-width:160px} table{width:100%;background:white;border-collapse:collapse;margin-top:15px} th,td{padding:10px;border-bottom:1px solid #ddd;text-align:left} a{color:#1e40af} .btn{background:#1e40af;color:white;padding:10px 15px;border-radius:8px;text-decoration:none} input,select{padding:10px;margin:5px;border:1px solid #ccc;border-radius:8px} .top{display:flex;align-items:center;gap:15px} .top img{width:70px}</style>
    <div class='top'><img src='/static/logo.png'><div><h2 style='margin:0'>Fast Media Graphic - Dashboard</h2><p style='margin:0'>{{name}} ({{role}}) | Bardnersville, Monrovia</p></div></div><br>
    <a class='btn' href='/add_order'>+ Add New Order</a> """ + ("<a class='btn' style='background:green' href='/add_expense'>+ Add Expense</a> " if admin else "") + """<a class='btn' style='background:#64748b' href='/logout'>Logout</a>
    <br><br>""" + money_html + """
    <h3>Orders</h3><table><tr><th>ID</th><th>Customer</th><th>Job</th><th>Qty</th><th>Price</th><th>Paid</th><th>Balance</th><th>Date</th><th>Action</th></tr>""" + rows + """</table>
    <h3>Expenses (Admin Only)</h3><table><tr><th>Item</th><th>Amount</th><th>Date</th><th>Note</th></tr>""" + exp_rows + """</table>
    """, name=session.get("name"), role=session.get("role"))

@app.route("/add_order", methods=["GET", "POST"])
def add_order():
    if "user" not in session: return redirect("/")
    if request.method == "POST":
        price = float(request.form.get("price") or 0)
        paid = float(request.form.get("paid") or 0)
        conn = get_db()
        conn.execute("INSERT INTO orders (customer,phone,job,size,qty,price,paid,balance,date,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (request.form.get("customer"), request.form.get("phone"), request.form.get("job"), request.form.get("size"),
             int(request.form.get("qty") or 1), price, paid, price-paid, str(date.today()), "Pending"))
        conn.commit()
        oid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return redirect(f"/receipt/{oid}")
    return render_template_string("""
    <style>body{font-family:Arial;background:#f1f5f9;padding:20px} .box{background:white;padding:25px;border-radius:12px;max-width:500px;margin:auto;text-align:center} .box img{width:100px} input,select{width:100%;padding:11px;margin:6px 0;border:1px solid #ccc;border-radius:8px;box-sizing:border-box} button{width:100%;padding:12px;background:#1e40af;color:white;border:none;border-radius:8px;font-weight:bold}</style>
    <div class='box'><img src='/static/logo.png'><h2>Fast Media Graphic</h2><h3>+ Add Order</h3><form method='post'>
    <input name='customer' placeholder='Customer Name' required><input name='phone' placeholder='Phone Number'>
    <select name='job'><option>Banner</option><option>T-Shirt</option><option>Flyer</option><option>Sticker</option><option>Business Card</option><option>Invitation</option><option>Other</option></select>
    <input name='size' placeholder='Size e.g. 10X12 / Large'><input type='number' name='qty' placeholder='Quantity' value='1'>
    <input type='number' step='0.01' name='price' placeholder='Total Price $' required>
    <input type='number' step='0.01' name='paid' placeholder='Amount Paid $' required>
    <button>SAVE & PRINT RECEIPT</button></form><br><a href='/dashboard'>Back to Dashboard</a></div>
    """)

@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():
    if not is_admin(): return "<h3>Access Denied - Admin Only</h3><a href='/dashboard'>Back</a>"
    if request.method == "POST":
        conn = get_db()
        conn.execute("INSERT INTO expenses (item,amount,date,note) VALUES (?,?,?,?)", (request.form.get("item"), float(request.form.get("amount") or 0), str(date.today()), request.form.get("note")))
        conn.commit(); conn.close()
        return redirect("/dashboard")
    return "<style>body{font-family:Arial;padding:20px}input{width:100%;padding:11px;margin:6px 0}button{padding:12px;background:green;color:white;border:none;border-radius:8px}</style><h2>Add Expense - Fast Media Graphic</h2><form method='post'><input name='item' placeholder='e.g. Ink, Flex Material' required><input name='amount' type='number' step='0.01' placeholder='Amount $' required><input name='note' placeholder='Note'><button>SAVE</button></form><br><a href='/dashboard'>Back</a>"

@app.route("/delete_order/<int:oid>")
def delete_order(oid):
    if not is_admin(): return "Access Denied - Workers cannot delete"
    conn = get_db(); conn.execute("DELETE FROM orders WHERE id=?", (oid,)); conn.commit(); conn.close()
    return redirect("/dashboard")

@app.route("/receipt/<int:oid>")
def receipt(oid):
    conn = get_db(); o = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone(); conn.close()
    if not o: return "Not found"
    unit = o["price"] / o["qty"] if o["qty"] else o["price"]
    return render_template_string("""
    <style>
    body{font-family:Arial;background:#eee;padding:20px}
    .paper{max-width:700px;margin:auto;background:white;padding:30px 35px}
    .top{text-align:center}
    .top img{width:150px}
    .top h1{font-size:38px;margin:5px 0 0 0}
    .top p{margin:2px;font-size:13px}
    .meta{display:flex;justify-content:space-between;margin-top:20px;font-weight:bold}
    .blue{background:#7aa7e8;color:white;padding:5px 10px;display:inline-block}
    table{width:100%;border-collapse:collapse;margin-top:15px}
    th{background:#7aa7e8;color:white;padding:10px}
    td{border:1px solid #999;padding:10px;text-align:center}
    td.desc{text-align:left;font-weight:bold}
    .total td{font-weight:bold}
    .sign{margin-top:40px;display:flex;justify-content:space-between}
    .footer{background:#2f6fd1;color:white;text-align:center;padding:6px;margin-top:20px;font-size:12px}
    @media print{body{background:white;padding:0} button,a{display:none}}
    </style>
    <div class='paper'>
      <div class='top'>
        <img src='/static/logo.png'>
        <h1>Fast Media Graphic</h1>
        <p>Bardnersville, Patience Shop</p>
        <p>Monrovia, Liberia</p>
        <p>Cell: 0770008720 / 0880450579 / 0776573725</p>
      </div>
      <div style='text-align:right;margin-top:10px'>Proforma ☐ &nbsp; Invoice ☐</div>
      <div class='meta'>
        <div><span class='blue'>Invoice #</span> {{o.id}}</div>
        <div>Date: <u><b>{{o.date}}</b></u></div>
      </div>
      <div style='margin-top:10px'><u>Invoice to:</u> <b>{{o.customer}}</b> &nbsp; {{o.phone}}</div>
      <table>
        <tr><th>No</th><th>Description</th><th>Qty</th><th>Unit Price (US $)</th><th>Amount (US $)</th></tr>
        <tr><td>1</td><td class='desc'>{{o.job}} {{o.size}}</td><td>{{o.qty}}</td><td>{{"%.2f"|format(unit)}}</td><td>{{"%.2f"|format(o.price)}}</td></tr>
        <tr><td>2</td><td></td><td></td><td></td><td></td></tr>
        <tr><td>3</td><td></td><td></td><td></td><td></td></tr>
        <tr class='total'><td colspan='4' style='text-align:right;background:#7aa7e8;color:white'>Grand Total</td><td>{{"%.2f"|format(o.price)}}</td></tr>
        <tr><td colspan='4' style='text-align:right'>Paid</td><td>{{"%.2f"|format(o.paid)}}</td></tr>
        <tr><td colspan='4' style='text-align:right'><b>Balance Owed</b></td><td><b>{{"%.2f"|format(o.balance)}}</b></td></tr>
      </table>
      <div class='sign'><div>_________________<br><small>Authorized Sign</small></div><div>_________________<br><small>Customer Sign</small></div></div>
      <div class='footer'>We serve with professionalism</div>
      <br><center><button onclick='window.print()' style='padding:12px 25px;background:#1e40af;color:white;border:none;border-radius:8px'>🖨️ PRINT RECEIPT</button> <a href='/dashboard'>Back</a></center>
    </div>
    """, o=o, unit=unit)

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))