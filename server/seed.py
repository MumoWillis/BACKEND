from flask import Blueprint, request, jsonify
from .models import db, Contact, Feedback

bp = Blueprint('main', __name__)

@bp.route('/contact-us', methods=['POST'])
def contact_us():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    message = data.get('message')

    if not all([name, email, message]):
        return jsonify({'message': 'Missing required fields'}), 400

    new_contact = Contact(name=name, email=email, phone=phone, message=message)
    db.session.add(new_contact)
    db.session.commit()

    return jsonify({'message': 'Message sent successfully!'}), 201

@bp.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    feedback_text = data.get('feedback')

    if not feedback_text:
        return jsonify({'message': 'Feedback cannot be empty'}), 400

    new_feedback = Feedback(feedback=feedback_text)
    db.session.add(new_feedback)
    db.session.commit()

    return jsonify({'message': 'Feedback submitted successfully!'}), 201


