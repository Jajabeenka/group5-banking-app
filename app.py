from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
import requests

app = Flask(__name__)

# Required for Flask Sessions (encrypts session cookies)
app.secret_key = "super_secret_key_change_in_production"

# ==========================================
# MySQL Database Configuration
# ==========================================
DB_USER = "group5user"
DB_PASSWORD = "YourStrongPassword123!"
DB_HOST = "<DATABASE_PRIVATE_IP>"  # Replace with DB EC2 Private IP
DB_NAME = "appdb"

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00)

# ==========================================
# Routes
# ==========================================

@app.route('/pay')
def pay():
    amount_due = request.args.get('amt', '0.00')
    return render_template('login.html', amount_due=amount_due)


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or request.form

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 'failed', 'message': 'Username and password required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'status': 'failed', 'message': 'Invalid credentials'}), 401

    # Store user identity in encrypted Flask session
    session['username'] = user.username

    return jsonify({'status': 'success', 'redirect': url_for('index')}), 200


@app.route('/index')
def index():
    # Retrieve logged-in user from session
    username = session.get('username')

    # If not logged in, send back to login page
    if not username:
        return redirect(url_for('pay'))

    # Fetch live balance directly from MySQL
    user = User.query.filter_by(username=username).first()
    current_balance = float(user.balance) if user and user.balance is not None else 0.00

    # Pass username and balance directly into index.html safely
    return render_template('index.html', username=username, balance=current_balance)


@app.route('/trigger-payment', methods=['POST'])
def trigger_payment():
    try:
        username = session.get('username')
        data = request.get_json(silent=True) or {}
        amount_due = float(data.get('amt', 0.0))

        updated_balance = 0.0

        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                current_balance = float(user.balance or 0.0)
                new_balance = max(0.0, current_balance - amount_due)
                user.balance = new_balance
                db.session.commit()
                updated_balance = float(user.balance)

        # External logging call
        try:
            requests.get('http://18.233.137.78/payment_success', params={'txn': 123}, timeout=5)
        except Exception as ext_e:
            print(f'External server warning: {ext_e}')

        return jsonify({'status': 'success', 'new_balance': updated_balance})

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'failed', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
