from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import stripe
import requests
import base64
from datetime import datetime
import os

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5173", "supports_credentials": True}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your-database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['STRIPE_SECRET_KEY'] = 'sk_test_51PSyfKFQpmwDMxbNY99dDObf8CfPcWkt5aaHBN51skNPi1aAj9MT1Y59pPBJCMrWwcaSrOOa49VmLAPXwU2SUo8L002o7T6lqj'  
app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_51PSyfKFQpmwDMxbNUdboNSzFeEY8qAiyBPykaV1GvELeMR565tXbJGZNwJ9c55WIy78WIhSkA0kwcdfGIDrijoh0003wwNOxoq'
app.config['MPESA_CONSUMER_KEY'] = 'jAQA3R1sHMjJAX6ycfEiHlJlb4SQAbvlFuyGgzCdUr0oOGBp'
app.config['MPESA_CONSUMER_SECRET'] = 'odLsaVRkGWYpsv5kT60Y8sExTYCGVH24BX22t0rz4gTBAnXmyXN3df4QXDXUncq4'
app.config['MPESA_SHORTCODE'] = '174379'
app.config['MPESA_PASSKEY'] = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
app.config['MPESA_CALLBACK_URL'] = 'https://yourdomain.com/mpesa/callback'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
stripe.api_key = app.config['STRIPE_SECRET_KEY']

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)


@app.route('/')
def index():
    return "Welcome to the Payment API"

@app.route('/favicon.ico')
def favicon():
    return '', 204

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

if __name__ == '__main__':
    app.run(debug=True)
