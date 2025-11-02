from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, bcrypt, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "your_secret_key"

db.init_app(app)
bcrypt.init_app(app)

# Create tables (run once)
with app.app_context():
    db.create_all()

# ---------------------------
# In-memory table status storage
# ---------------------------
# key = table_number, value = "free" or "occupied"
table_statuses = {i: "free" for i in range(1, 11)}

# ---------------------------
# ROUTES
# ---------------------------

# Home page
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('auth.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('home'))
    return render_template('index.html', username=session['username'])

# Signup
@app.route('/signup', methods=['POST'])
def signup():
    fullname = request.form['fullname']
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        flash("Passwords do not match!", "danger")
        return redirect(url_for('home'))

    if User.query.filter_by(username=username).first():
        flash("Username already exists!", "danger")
        return redirect(url_for('home'))

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(fullname=fullname, username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    flash("Account created successfully! Please login.", "success")
    return redirect(url_for('home'))

# Login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        session['username'] = user.username
        flash("Login successful!", "success")
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid username or password!", "danger")
        return redirect(url_for('home'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# ---------------------------
# Additional Pages
# ---------------------------

@app.route('/viewMenu')
def view_menu():
    if 'username' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('home'))
    # Pass table statuses so front-end can show available/reserved tables
    return render_template('viewMenu.html', table_statuses=table_statuses)

@app.route('/placeOrder')
def place_order():
    if 'username' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('home'))
    return render_template('placeOrder.html')

@app.route('/viewOrders')
def view_orders():
    if 'username' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('home'))
    return render_template('viewOrders.html')

@app.route('/GenerateBill')
def generate_bill():
    if 'username' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('home'))
    return render_template('GenerateBill.html')

# ---------------------------
# Table Status Routes
# ---------------------------
@app.route('/tableStatus')
def table_status():
    if 'username' not in session:
        flash("Please login first!", "warning")
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

@app.route('/generateAccount')
def generate_account():
    if 'username' not in session:
        flash("Please login first!", "warning")
        return redirect(url_for('home'))
    return render_template('generateAccount.html')

# ---------------------------
# RUN SERVER
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
