from flask import Blueprint, request, jsonify
from models import db, Order
import logging
from daraja import lipa_na_mpesa_online

api = Blueprint('api', __name__)

# Function to convert amount to float if it's a string
def convert_amount_to_float(amount):
    if isinstance(amount, str):
        # Remove 'KSH' prefix and any commas
        amount = amount.replace('KSH', '').replace(',', '').strip()
        return float(amount)
    return amount

@api.route('/place-order', methods=['POST'])
def place_order():
    try:
        data = request.json
    
        amount = convert_amount_to_float(data['total_amount'])

        order = Order(
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            address1=data['address1'],
            address2=data.get('address2'),
            mpesa_number=data['mpesa_number'],
            amount=amount,
        )
        db.session.add(order)
        db.session.commit()

        response = lipa_na_mpesa_online(
            amount=order.amount,
            phone_number=order.mpesa_number,
            account_reference=order.id,
            transaction_desc=f'Payment for Order {order.id}'
        )

        if response is None or response.get('ResponseCode') != '0':
            order.status = 'failed'
            db.session.commit()
            return jsonify({'error': 'Payment failed'}), 500

        order.status = 'processing'
        db.session.commit()
        return jsonify({'message': 'Payment processing', 'order_id': order.id}), 200

    except Exception as e:
        db.session.rollback()  # Rollback the transaction on failure
        logging.error(f"Failed to place order: {e}")
        return jsonify({'error': 'Failed to place order'}), 500
