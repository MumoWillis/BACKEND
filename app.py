from flask import Flask, jsonify, request, redirect, url_for, session, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from config import Config
import stripe
import requests
import base64
from datetime import datetime
import hashlib
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
oauth = OAuth(app)
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# CORS configuration
CORS(app, resources={r"/api/*": {
    "origins": ["http://127.0.0.1:5173", "http://localhost:5173"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True
}})

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

def _build_cors_preflight_response():
    response = jsonify({"message": "Preflight request handled"})
    response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin"))
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response, 200

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin"))
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

@app.after_request
def after_request(response):
    return _corsify_actual_response(response)

# Root route
@app.route('/')
def index():
    return jsonify({'message': 'Welcome to the API!'})

# Auth Blueprint
auth = Blueprint('auth', __name__)

# OAuth configuration for Google
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'email'},
)

# Password hashing utilities
def generate_password_hash(password):
    salt = os.urandom(16)
    return salt + hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

def check_password_hash(stored_password, provided_password):
    salt = stored_password[:16]
    stored_key = stored_password[16:]
    provided_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100000)
    return provided_key == stored_key

# User signup
@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    existing_user = User.query.filter_by(email=data['email']).first()

    if existing_user:
        return jsonify({'message': 'User already exists!'}), 409

    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Account created successfully!'}), 201

# User login
@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password, data['password']):
        session['user_id'] = user.id  # Storing the user's ID in session
        return jsonify({'message': 'Login successful!'})
    else:
        return jsonify({'message': 'Invalid credentials!'}), 401

# User logout
@auth.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  # Removing the user's ID from session
    return jsonify({'message': 'Logged out successfully!'})

# Google OAuth login
@auth.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.authorized', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth.route('/login/google/authorized')
def authorized():
    token = google.authorize_access_token()
    if token is None:
        return 'Access denied: error={} description={}'.format(
            request.args.get('error'),
            request.args.get('error_description')
        )
    
    user_info = google.get('userinfo').json()
    email = user_info['email']
    user = User.query.filter_by(email=email).first()
    
    if not user:
        user = User(username=email.split('@')[0], email=email)
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id  # Storing the user's ID in session
    session['google_token'] = token

    return redirect(url_for('index'))

# Register the auth blueprint
app.register_blueprint(auth, url_prefix='/api')

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.LargeBinary, nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)

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
def generate_mpesa_password(shortcode, passkey, timestamp):
    data = shortcode + passkey + timestamp
    encoded = base64.b64encode(data.encode())
    return encoded.decode('utf-8')

def get_mpesa_access_token(consumer_key, consumer_secret):
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    response = requests.get(api_url, auth=(consumer_key, consumer_secret))
    json_response = response.json()
    return json_response['access_token']

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

if __name__ == '__main__':
    app.run(debug=True)
