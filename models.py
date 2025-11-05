from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import json

db = SQLAlchemy()
bcrypt = Bcrypt()

# ----------------------------
# USER MODEL
# ----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='waiter')  # Added role field

    def __repr__(self):
        return f"<User {self.username}>"

# ----------------------------
# BILL MODEL
# ----------------------------
class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, nullable=False)
    items = db.Column(db.Text, nullable=False)  # Store items as JSON string
    total = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def get_items(self):
        """Convert JSON string back to Python list"""
        try:
            return json.loads(self.items)
        except Exception:
            return []

    def __repr__(self):
        return f"<Bill Table {self.table_number} | Rs.{self.total}>"

    # ----------------------------
    # REPORT HELPER METHODS
    # ----------------------------
    @staticmethod
    def get_daily_income():
        """Return total income for the current day"""
        today = datetime.utcnow().date()
        bills_today = Bill.query.filter(
            db.func.date(Bill.timestamp) == today
        ).all()
        return sum(b.total for b in bills_today)

    @staticmethod
    def get_monthly_income():
        """Return total income for the current month"""
        now = datetime.utcnow()
        bills_month = Bill.query.filter(
            db.extract('year', Bill.timestamp) == now.year,
            db.extract('month', Bill.timestamp) == now.month
        ).all()
        return sum(b.total for b in bills_month)

    @staticmethod
    def get_all_bills():
        """Return all bills sorted by date (newest first)"""
        return Bill.query.order_by(Bill.timestamp.desc()).all()
