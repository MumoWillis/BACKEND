import os
import base64
import hashlib
import requests
from datetime import datetime

from flask import Flask, jsonify, request, session, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import stripe

# Initialize Flask app
app = Flask(__name__)

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'your-stripe-secret-key'
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'your-stripe-public-key'
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY') or 'your-mpesa-consumer-key'
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET') or 'your-mpesa-consumer-secret'
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE') or 'your-mpesa-shortcode'
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY') or 'your-mpesa-passkey'
    MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL') or 'your-mpesa-callback-url'

app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
stripe.api_key = app.config['STRIPE_SECRET_KEY']
CORS(app, resources={r"/api/*": {"origins": ["http://127.0.0.1:5173", "http://localhost:5173"]}})

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)

# Utilities
def generate_mpesa_password(shortcode, passkey, timestamp):
    data = shortcode + passkey + timestamp
    encoded = base64.b64encode(data.encode())
    return encoded.decode('utf-8')

def get_mpesa_access_token(consumer_key, consumer_secret):
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    response = requests.get(api_url, auth=(consumer_key, consumer_secret))
    json_response = response.json()
    return json_response['access_token']

# Auth Blueprint
auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    existing_user = User.query.filter_by(email=data['email']).first()

    if existing_user:
        return jsonify({'message': 'User already exists!'}), 409

    new_user = User(username=data['username'], email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Account created successfully!'}), 201

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful!'})
    return jsonify({'message': 'Invalid credentials!'}), 401

@auth.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully!'})

app.register_blueprint(auth, url_prefix='/api')

# Stripe Payment Routes
@app.route('/stripe-key', methods=['GET'])
def get_stripe_key():
    return jsonify({'publicKey': app.config['STRIPE_PUBLIC_KEY']})

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    data = request.json
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(data['amount']),
            currency=data['currency'],
            receipt_email=data['email'],
            metadata={'integration_check': 'accept_a_payment'},
        )
        order = Order(
            email=data['email'],
            amount=int(data['amount']),
            currency=data['currency'],
            payment_status='Pending'
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({'clientSecret': intent['client_secret']})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/confirm-payment/<int:order_id>', methods=['POST'])
def confirm_payment(order_id):
    order = Order.query.get_or_404(order_id)
    order.payment_status = 'Confirmed'
    db.session.commit()
    return jsonify({'message': 'Payment confirmed'})

@app.route('/order-status/<int:order_id>', methods=['GET'])
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        'order_id': order.id,
        'email': order.email,
        'amount': order.amount,
        'currency': order.currency,
        'payment_status': order.payment_status
    })

# MPESA Integration
@app.route('/mpesa-payment', methods=['POST'])
def mpesa_payment():
    data = request.json
    access_token = get_mpesa_access_token(app.config['MPESA_CONSUMER_KEY'], app.config['MPESA_CONSUMER_SECRET'])
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {'Authorization': f'Bearer {access_token}'}
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_mpesa_password(app.config['MPESA_SHORTCODE'], app.config['MPESA_PASSKEY'], timestamp)
    request_data = {
        'BusinessShortCode': app.config['MPESA_SHORTCODE'],
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': data['amount'],
        'PartyA': data['phone_number'],
        'PartyB': app.config['MPESA_SHORTCODE'],
        'PhoneNumber': data['phone_number'],
        'CallBackURL': app.config['MPESA_CALLBACK_URL'],
        'AccountReference': 'Order',
        'TransactionDesc': 'Payment for order'
    }
    response = requests.post(api_url, json=request_data, headers=headers)
    return jsonify(response.json())

# Root route
@app.route('/')
def index():
    return jsonify({'message': 'Welcome to the API!'})

if __name__ == '__main__':
    app.run(debug=True)
