from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
import requests

# template_folder='.' keeps index.html side-by-side with app.py if needed
app = Flask(__name__)

# ==========================================
# MySQL Database Configuration
# ==========================================
DB_USER = "group5user"             # Replace with your MySQL username
DB_PASSWORD = "group5db123" # Replace with your MySQL user's password
DB_HOST = "10.0.1.202"  # Replace with DB EC2's Private IP (e.g., 10.0.1.100)
DB_NAME = "appdb"

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# Database Model
# ==========================================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00)  # Added balance column

# ==========================================
# Routes
# ==========================================

@app.route('/pay')
def pay():
    # Capture the 'amt' parameter from the URL (e.g., /pay?amt=1500)
    # Default to '0.00' if it doesn't exist
    amount_due = request.args.get('amt', '0.00')

    # Pass the amount into your login.html template
    return render_template('login.html', amount_due=amount_due)


@app.route('/login', methods=['POST'])
def login():
    # Accepts input from either JSON (JS fetch) or standard HTML form submit
    data = request.get_json(silent=True) or request.form

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        if request.is_json:
            return jsonify({'status': 'failed', 'message': 'Username and password required'}), 400
        return "Username and password required", 400

    # Query user from MySQL database
    user = User.query.filter_by(username=username).first()

    # Verify user exists and check password hash
    if not user or not check_password_hash(user.password_hash, password):
        if request.is_json:
            return jsonify({'status': 'failed', 'message': 'Invalid credentials'}), 401
        return "Invalid username or password", 401

    # Successful login response
    if request.is_json:
        return jsonify({
            'status': 'success',
            'redirect': url_for('index'),
            'user': {
                'id': user.id,
                'username': user.username,
                'balance': float(user.balance) if user.balance is not None else 0.00
            }
        }), 200

    return redirect(url_for('index'))


@app.route('/index')
def index():
    # Serves the index page when login succeeds or redirect triggers
    return render_template('index.html')


@app.route('/trigger-payment', methods=['POST'])
def trigger_payment():
    try:
        data = request.get_json(silent=True) or {}
        username = data.get('username')
        amount_due = float(data.get('amt', 0.0))

        updated_balance = 0.0

        # Query user from MySQL database
        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                current_balance = float(user.balance or 0.0)
                # Deduct amount from balance (prevent negative balance)
                new_balance = max(0.0, current_balance - amount_due)
                user.balance = new_balance

                # Commit change to MySQL
                db.session.commit()
                updated_balance = float(user.balance)

        # Hit target transaction logging server
        try:
            requests.get('http://18.233.137.78/payment_success', params={'txn': 123}, timeout=5)
        except Exception as ext_e:
            print(f'External server warning: {ext_e}')

        return jsonify({
            'status': 'success',
            'new_balance': updated_balance
        })

    except Exception as e:
        db.session.rollback()  # Roll back DB changes if an error occurs
        print(f'Payment DB error: {e}')
        return jsonify({'status': 'failed', 'error': str(e)}), 500


if __name__ == '__main__':
    # host='0.0.0.0' allows external web traffic to reach Flask on your EC2 instance
    app.run(host='0.0.0.0', port=5000, debug=True)
 
