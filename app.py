from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, bcrypt, User, Bill
from config import Config
from datetime import datetime
import json

# ---------------------------
# APP CONFIGURATION
# ---------------------------
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "your_secret_key"

db.init_app(app)
bcrypt.init_app(app)

# ---------------------------
# CREATE DATABASE TABLES
# ---------------------------
with app.app_context():
    db.create_all()

# ---------------------------
# TABLE STATUS MEMORY STORE
# ---------------------------
table_statuses = {i: "free" for i in range(1, 11)}

# ---------------------------
# HOME & DASHBOARD
# ---------------------------
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('auth.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('logout'))

    # Redirect according to role
    if user.role == 'admin':
        return render_template('index.html', username=user.username)
    elif user.role == 'waiter':
        return render_template('waiter.html', username=user.username)
    else:
        flash("Invalid role detected!", "danger")
        return redirect(url_for('logout'))

# ---------------------------
# AUTHENTICATION ROUTES
# ---------------------------
@app.route('/signup', methods=['POST'])
def signup():
    fullname = request.form.get('fullname')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    role = request.form.get('role', 'waiter')

    if password != confirm_password:
        flash("Passwords do not match!", "danger")
        return redirect(url_for('home'))

    if User.query.filter_by(username=username).first():
        flash("Username already exists!", "danger")
        return redirect(url_for('home'))

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(fullname=fullname, username=username, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    flash(f"{role.capitalize()} account created successfully! Please login.", "success")
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password, password):
        session['username'] = user.username
        flash("Login successful!", "success")

        # Redirect based on role
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'waiter':
            return redirect(url_for('waiter_dashboard'))
        else:
            flash("Unknown role!", "danger")
            return redirect(url_for('logout'))
    else:
        flash("Invalid username or password!", "danger")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# ---------------------------
# SEPARATE DASHBOARDS
# ---------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'admin':
        flash("Access denied!", "danger")
        return redirect(url_for('dashboard'))

    return render_template('index.html', username=user.username)

@app.route('/waiter/dashboard')
def waiter_dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'waiter':
        flash("Access denied!", "danger")
        return redirect(url_for('dashboard'))

    return render_template('waiter.html', username=user.username)

# ---------------------------
# ADMIN: ACCOUNT GENERATION
# ---------------------------
@app.route('/generateAccount')
def generate_account():
    if 'username' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()
    if user.role != 'admin':
        flash("Only Admin can create waiter accounts!", "danger")
        return redirect(url_for('dashboard'))

    return render_template('generateAccount.html')

@app.route('/createWaiter', methods=['POST'])
def create_waiter():
    if 'username' not in session:
        return redirect(url_for('home'))

    admin = User.query.filter_by(username=session['username']).first()
    if admin.role != 'admin':
        flash("Only Admin can create waiter accounts!", "danger")
        return redirect(url_for('dashboard'))

    fullname = request.form.get('fullname')
    username = request.form.get('username')
    password = request.form.get('password')

    if User.query.filter_by(username=username).first():
        flash("Waiter username already exists!", "danger")
        return redirect(url_for('generate_account'))

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_waiter = User(fullname=fullname, username=username, password=hashed_password, role='waiter')
    db.session.add(new_waiter)
    db.session.commit()

    flash("Waiter account created successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# ---------------------------
# PAGE ROUTES
# ---------------------------
@app.route('/viewMenu')
def view_menu():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('viewMenu.html')

@app.route('/manageMenu')
def manage_menu():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('manageMenu.html')

@app.route('/placeOrder')
def place_order():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('placeOrder.html')

@app.route('/viewOrders')
def view_orders():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('viewOrders.html')

@app.route('/GenerateBill')
def generate_bill():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('GenerateBill.html')

# ---------------------------
# BILL HANDLING
# ---------------------------
@app.route('/saveBill', methods=['POST'])
def save_bill():
    try:
        data = request.get_json()
        table_number = data.get("table_number")
        items = data.get("items", [])
        total = float(data.get("total", 0.0))

        new_bill = Bill(
            table_number=table_number,
            items=json.dumps(items),
            total=total,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_bill)
        db.session.commit()

        return jsonify({"success": True, "message": "Bill saved successfully!"})
    except Exception as e:
        print("Error saving bill:", e)
        return jsonify({"success": False, "message": "Error saving bill"}), 500

# ---------------------------
# REPORT GENERATION
# ---------------------------
@app.route('/report')
def report():
    if 'username' not in session:
        return redirect(url_for('home'))

    bills = Bill.query.order_by(Bill.timestamp.desc()).all()
    today = datetime.utcnow().date()
    current_month = today.month
    current_year = today.year

    daily_income = sum(b.total for b in bills if b.timestamp.date() == today)
    monthly_income = sum(b.total for b in bills if b.timestamp.month == current_month and b.timestamp.year == current_year)

    for b in bills:
        try:
            b.items = json.loads(b.items)
        except:
            b.items = []

    return render_template(
        'report.html',
        reports=bills,
        daily_income=daily_income,
        monthly_income=monthly_income
    )

# ---------------------------
# TABLE STATUS
# ---------------------------
@app.route('/tableStatus')
def table_status():
    if 'username' not in session:
        return redirect(url_for('home'))
    tables = [{"number": num, "status": status} for num, status in table_statuses.items()]
    return render_template('tableStatus.html', tables=tables)

@app.route('/reserveTable/<int:table_number>', methods=['POST'])
def reserve_table(table_number):
    table_statuses[table_number] = "occupied"
    return jsonify({"success": True, "table": table_number, "status": "occupied"})

@app.route('/freeTable/<int:table_number>', methods=['POST'])
def free_table(table_number):
    table_statuses[table_number] = "free"
    return jsonify({"success": True, "table": table_number, "status": "free"})

# ---------------------------
# RUN APP
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
