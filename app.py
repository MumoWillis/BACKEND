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
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
oauth = OAuth(app)
stripe.api_key = app.config['STRIPE_SECRET_KEY']

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

# Route for the root URL
@app.route('/')
def index():
    return jsonify({'message': 'Welcome to the API!'})

# Auth routes and logic
auth = Blueprint('auth', __name__)  

google = oauth.register(
    name='google',
    client_id='your_google_client_id',
    client_secret='your_google_client_secret',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'email'},
)

@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    existing_user = User.query.filter_by(email=data['email']).first()

    if existing_user:
        return jsonify({'message': 'User already exists!'}), 409

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Account created successfully!'}), 201

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        session['user_id'] = user.id  # Storing the user's ID in session
        return jsonify({'message': 'Login successful!'})
    else:
        return jsonify({'message': 'Invalid credentials!'}), 401

@auth.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  # Removing the user's ID from session
    return jsonify({'message': 'Logged out successfully!'})

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

# Routes for Payment Integration
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
    response_data = response.json()
    if response_data.get('ResponseCode') == '0':
        return jsonify({'message': 'Payment request successful', 'CheckoutRequestID': response_data['CheckoutRequestID']})
    else:
        return jsonify({'error': response_data.get('errorMessage', 'Payment request failed')}), 400

@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.json
    print("Callback Data: ", data)
    if 'Body' in data and 'stkCallback' in data['Body']:
        callback_data = data['Body']['stkCallback']
        result_code = callback_data['ResultCode']
        result_desc = callback_data['ResultDesc']
        checkout_request_id = callback_data['CheckoutRequestID']
        if result_code == 0:
            print("Payment successful:", result_desc)
        else:
            print("Payment failed:", result_desc)
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})
    else:
        print("Unexpected callback data:", data)
        return jsonify({"ResultCode": 1, "ResultDesc": "Rejected"})

# Correct conditional check for main
if __name__ == '__main__':
    app.run(debug=True)
